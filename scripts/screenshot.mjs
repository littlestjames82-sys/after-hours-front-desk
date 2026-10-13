// Capture honest evidence screenshots of the simulator via CDP.
// Usage: node scripts/screenshot.mjs <url> <out.png>
// Launches headless Chromium, loads the page (use ?demo=mid or ?demo=full),
// waits for window.__demoState === 'done', then screenshots the full page.
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";

const [url, out] = process.argv.slice(2);
const CHROME = process.env.CHROME_BIN || "/opt/meta-chromium/chrome";
const PORT = 9333;

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--no-proxy-server",
  "--disable-features=LocalNetworkAccessChecks",
  `--remote-debugging-port=${PORT}`, "--window-size=900,1400", url,
], { stdio: "ignore" });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function cdp() {
  for (let i = 0; i < 60; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const targets = await r.json();
      const page = targets.find(t => t.type === "page" && t.url === url);
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* not up yet */ }
    await sleep(1000);
  }
  throw new Error("chrome devtools did not come up");
}

let msgId = 0;
const pending = new Map();
const ws = new WebSocket(await cdp());
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
await new Promise(r => ws.onopen = r);
function send(method, params = {}) {
  return new Promise(res => {
    const id = ++msgId;
    pending.set(id, res);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

await send("Page.enable");
await send("Runtime.enable");

let state = "";
for (let i = 0; i < 110; i++) {
  await sleep(5000);
  const r = await send("Runtime.evaluate", {
    expression: "window.__demoState || 'none'", returnByValue: true });
  state = r.result?.result?.value ?? "";
  process.stdout.write(`\rstate: ${state}        `);
  if (state === "done" || String(state).startsWith("error")) break;
}
console.log("");
if (state !== "done") { console.error("demo did not finish:", state); process.exit(1); }

await sleep(1500); // let the summary card paint
const dims = await send("Runtime.evaluate", {
  expression: "({w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight})",
  returnByValue: true });
const { w, h } = dims.result.result.value;
const shot = await send("Page.captureScreenshot", {
  format: "png", captureBeyondViewport: true,
  clip: { x: 0, y: 0, width: w, height: h, scale: 1 } });
writeFileSync(out, Buffer.from(shot.result.data, "base64"));
console.log("saved", out, `${w}x${h}`);
ws.close();
chrome.kill();
process.exit(0);
