const allowedSubdomains = [
  "1705-david",
  "add-recipe",
  "auction-advisor",
  "blog",
  "cleaning-schedule",
  "compare-achievements",
  "connect-4",
  "directory",
  "drive-status",
  "enderle-cattle-co",
  "email-link-generator",
  "family-recipes",
  "flash-cards",
  "google-drive-viewer",
  "home-page-api",
  "home-page",
  "lost",
  "utilities",
  "puzzles",
  "scorekeeping-br-rounds",
  "woodworking-projects",
  // "www",
];

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const hostParts = url.hostname.split(".");
    
    if (hostParts.length < 3) {
      // no subdomain (like my-domain.com) — optionally redirect
      return fetch(request);
    }

    const subdomain = hostParts[0];

    if (!allowedSubdomains.includes(subdomain)) {
      return Response.redirect(
        `https://lost.ryan-brock.com?from=${encodeURIComponent(subdomain)}`,
        302
      );
    }

    return fetch(request);
  },
};
