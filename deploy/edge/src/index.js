// canon.tn07.dev edge proxy.
// Agent and API paths go straight to Cloud Run (no Hosting buffering, longer
// timeouts for MCP); everything else goes to the Firebase Hosting site.
// Cloud Run routes by Host, so we rewrite the URL rather than CNAME it.

const RUN = "canon-ezvux7gqxa-el.a.run.app";
const HOSTING = "canon-tn07.web.app";
const RUN_PREFIXES = ["/api/", "/mcp", "/a2a", "/hooks/", "/discord/", "/.well-known/", "/health"];

// Cloud Monitoring webhook -> Discord. Monitoring posts its own JSON, which a
// Discord webhook rejects, so we reformat here. Lives on Cloudflare, not Cloud
// Run, so "Canon is down" still gets delivered when Cloud Run is the problem.
// Secrets: ALERT_TOKEN (in the channel URL as ?token=) and DISCORD_WEBHOOK.
async function relayAlert(request, env) {
  const url = new URL(request.url);
  if (request.method !== "POST" || !env.ALERT_TOKEN || url.searchParams.get("token") !== env.ALERT_TOKEN) {
    return new Response("forbidden", { status: 403 });
  }
  const body = await request.json().catch(() => ({}));
  const i = body.incident || {};
  const open = i.state !== "closed";
  const content = [
    `${open ? "**ALERT**" : "Resolved"}: ${i.policy_name || "Canon"}`,
    i.summary || i.condition_name || "",
    i.url ? `<${i.url}>` : "",
  ].filter(Boolean).join("\n").slice(0, 1900);
  const r = await fetch(env.DISCORD_WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, allowed_mentions: { parse: [] } }),
  });
  return new Response(r.ok ? "ok" : "discord error", { status: r.ok ? 200 : 502 });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/_alert") return relayAlert(request, env);
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
