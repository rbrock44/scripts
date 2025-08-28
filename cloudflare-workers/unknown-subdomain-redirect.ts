const allowedSubdomains = [
  "1705-david",
  "add-recipe",
  "auction-advisor",
  "cleaning-schedule",
  "compare-achievements",
  "connect-4",
  "directory",
  "drive-status",
  "email-link-generator",
  "family-recipes",
  "flash-cards",
  "google-drive-viewer",
  "home-page-api",
  "home-page",
  "lost",
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
      return Response.redirect("https://lost.my-domain.com", 302);
    }

    return fetch(request);
  },
};
