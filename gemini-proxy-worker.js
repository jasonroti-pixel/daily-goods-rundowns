/**
 * Gemini proxy — Cloudflare Worker
 * ---------------------------------
 * Holds the Gemini API key as an encrypted secret (env.GEMINI_KEY) so it is
 * NEVER in the public repo or the page source. The summarizer page POSTs its
 * Gemini request body here; this Worker injects the key and forwards it to
 * Google, then returns Google's response. That's why the key can't leak:
 * browsers only ever see this Worker's URL, not the key.
 *
 * Deploy: see the step-by-step in the chat. In short —
 *   1. Create a free Worker at dash.cloudflare.com (Workers & Pages).
 *   2. Paste this entire file as the Worker code and Deploy.
 *   3. Add a Secret named  GEMINI_KEY  = your fresh Gemini key.
 *   4. Copy the Worker URL (https://<name>.<you>.workers.dev) and send it back.
 */
export default {
  async fetch(request, env) {
    const cors = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (request.method !== "POST") {
      return new Response("POST only", { status: 405, headers: cors });
    }
    if (!env.GEMINI_KEY) {
      return new Response(JSON.stringify({ error: { message: "Worker missing GEMINI_KEY secret." } }),
        { status: 500, headers: { ...cors, "Content-Type": "application/json" } });
    }

    // Model comes from ?model=... ; default to a current free-tier model.
    const model = new URL(request.url).searchParams.get("model") || "gemini-2.5-flash";
    const body = await request.text();

    const upstream = "https://generativelanguage.googleapis.com/v1beta/models/" +
      encodeURIComponent(model) + ":generateContent";

    let res;
    try {
      res = await fetch(upstream, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": env.GEMINI_KEY },
        body,
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: { message: "Upstream fetch failed: " + e.message } }),
        { status: 502, headers: { ...cors, "Content-Type": "application/json" } });
    }

    const text = await res.text();
    return new Response(text, {
      status: res.status,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  },
};
