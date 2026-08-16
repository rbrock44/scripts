// View and like counts for blog.ryan-brock.com.
//
// Runs on the route blog.ryan-brock.com/api/* which is more specific than the
// *.ryan-brock.com/* route used by unknown-subdomain-redirect.ts, so this worker
// wins for /api/ and that one never sees these requests.
//
//   GET  /api/counts/:slug   -> { views, likes, liked }
//   POST /api/views/:slug    -> { views }        once per visitor per day
//   POST /api/likes/:slug    -> { likes, liked } toggles, one like per visitor
//
// Requires a KV namespace bound as COUNTERS. Keys stored:
//   views:<slug>            counter
//   likes:<slug>            counter
//   view:<slug>:<visitor>   24h guard so refreshing does not inflate views
//   like:<slug>:<visitor>   idempotency guard, 1 year

const ALLOWED_ORIGIN = "https://blog.ryan-brock.com";

const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const VIEW_WINDOW_SECONDS = 60 * 60 * 24;
const LIKE_TTL_SECONDS = 60 * 60 * 24 * 365;

// Counting crawlers would make the numbers meaningless on a blog built to be crawled.
const BOT_PATTERN =
  /bot|crawler|spider|crawling|slurp|facebookexternalhit|embedly|quora link preview|showyoubot|outbrain|pinterest|vkshare|w3c_validator|whatsapp|flipboard|tumblr|bitlybot|skypeuripreview|nuzzel|discord|google|baidu|bing|yandex|duckduck|semrush|ahrefs|lighthouse|headless/i;

interface Env {
  COUNTERS: KVNamespace;
}

const CORS = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age": "86400",
  Vary: "Origin",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...CORS },
  });
}

// A stable-but-anonymous visitor id. The IP is hashed together with the slug so the
// same person cannot be correlated across posts, and the raw IP is never stored.
async function visitorId(request: Request, slug: string): Promise<string> {
  const ip = request.headers.get("CF-Connecting-IP") ?? "0.0.0.0";
  const agent = request.headers.get("User-Agent") ?? "";
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(`${slug}:${ip}:${agent}`)
  );

  return [...new Uint8Array(digest)]
    .slice(0, 12)
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function readCount(env: Env, key: string): Promise<number> {
  const value = await env.COUNTERS.get(key);
  return value ? Number(value) : 0;
}

async function bumpCount(env: Env, key: string, delta: number): Promise<number> {
  const next = Math.max(0, (await readCount(env, key)) + delta);
  await env.COUNTERS.put(key, String(next));
  return next;
}

async function handleCounts(env: Env, slug: string, visitor: string): Promise<Response> {
  const [views, likes, liked] = await Promise.all([
    readCount(env, `views:${slug}`),
    readCount(env, `likes:${slug}`),
    env.COUNTERS.get(`like:${slug}:${visitor}`),
  ]);

  return json({ views, likes, liked: liked !== null });
}

async function handleView(
  request: Request,
  env: Env,
  slug: string,
  visitor: string
): Promise<Response> {
  if (BOT_PATTERN.test(request.headers.get("User-Agent") ?? "")) {
    return json({ views: await readCount(env, `views:${slug}`) });
  }

  const guard = `view:${slug}:${visitor}`;
  if (await env.COUNTERS.get(guard)) {
    return json({ views: await readCount(env, `views:${slug}`) });
  }

  await env.COUNTERS.put(guard, "1", { expirationTtl: VIEW_WINDOW_SECONDS });
  return json({ views: await bumpCount(env, `views:${slug}`, 1) });
}

async function handleLike(env: Env, slug: string, visitor: string): Promise<Response> {
  const guard = `like:${slug}:${visitor}`;
  const alreadyLiked = (await env.COUNTERS.get(guard)) !== null;

  if (alreadyLiked) {
    await env.COUNTERS.delete(guard);
    return json({ likes: await bumpCount(env, `likes:${slug}`, -1), liked: false });
  }

  await env.COUNTERS.put(guard, "1", { expirationTtl: LIKE_TTL_SECONDS });
  return json({ likes: await bumpCount(env, `likes:${slug}`, 1), liked: true });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    const url = new URL(request.url);
    const match = /^\/api\/(counts|views|likes)\/([^/]+)$/.exec(url.pathname);

    if (!match) {
      return json({ error: "not found" }, 404);
    }

    const [, action, slug] = match;
    if (!SLUG_PATTERN.test(slug)) {
      return json({ error: "bad slug" }, 400);
    }

    const visitor = await visitorId(request, slug);

    if (request.method === "GET" && action === "counts") {
      return handleCounts(env, slug, visitor);
    }
    if (request.method === "POST" && action === "views") {
      return handleView(request, env, slug, visitor);
    }
    if (request.method === "POST" && action === "likes") {
      return handleLike(env, slug, visitor);
    }

    return json({ error: "method not allowed" }, 405);
  },
};
