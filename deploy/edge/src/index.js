// canon.tn07.dev edge proxy.
// Agent and API paths go straight to Cloud Run (no Hosting buffering, longer
// timeouts for MCP); everything else goes to the Firebase Hosting site.
// Cloud Run routes by Host, so we rewrite the URL rather than CNAME it.

const RUN = "canon-ezvux7gqxa-el.a.run.app";
const HOSTING = "canon-tn07.web.app";
const RUN_PREFIXES = ["/api/", "/mcp", "/a2a", "/hooks/", "/discord/", "/.well-known/", "/health"];

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const clientHost = url.host;
    url.protocol = "https:";
    url.port = "";
    url.host = RUN_PREFIXES.some((p) => url.pathname.startsWith(p)) ? RUN : HOSTING;

    const proxied = new Request(url, request);
    proxied.headers.set("X-Forwarded-Host", clientHost);
    proxied.headers.set("X-Forwarded-Proto", "https");
    const response = await fetch(proxied);

    const location = response.headers.get("Location");
    if (location) {
      try {
        const target = new URL(location, url);
        if (target.host === RUN || target.host === HOSTING) {
          target.host = clientHost;
          const rewritten = new Response(response.body, response);
          rewritten.headers.set("Location", target.toString());
          return rewritten;
        }
      } catch {
        // unparseable Location: pass through
      }
    }
    return response;
  },
};
