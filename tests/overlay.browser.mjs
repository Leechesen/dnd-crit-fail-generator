import { chromium } from "playwright";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { OVERLAY_THEMES } from "../overlay-themes.mjs";
import { selections } from "../critfail-core.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const shots = process.env.KRITFAILER_SCREENSHOTS || path.join(root, "../screenshots");
await fs.mkdir(shots, { recursive: true });
const dataset = JSON.parse(await fs.readFile(path.join(root, "crit_fails.json"), "utf8"));
const entries = selections(dataset).flatMap(choice => Object.values(choice.severityMap).flatMap(pool => pool.map(entry => ({ title: choice.label, effect: entry.effect }))));
const longest = [...entries].sort((a, b) => b.effect.length - a.effect.length).slice(0, 50);
const server = http.createServer(async (request, response) => {
  const url = new URL(request.url, "http://localhost");
  try {
    const file = path.resolve(root, "." + url.pathname);
    if (!file.startsWith(root)) throw new Error("path");
    response.setHeader("Content-Type", url.pathname.endsWith(".mjs") ? "text/javascript" : "text/html; charset=utf-8");
    response.end(await fs.readFile(file));
  } catch { response.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, executablePath: process.env.KRITFAILER_CHROMIUM_EXECUTABLE });
const page = await browser.newPage({ viewport: { width: 3840, height: 2160 } });
const errors = [];
page.on("pageerror", error => errors.push(error.message));
await page.route("**/firebase-client.mjs", route => route.fulfill({ contentType: "text/javascript", body: `
  export const connectFirebase = async () => ({db:{}});
  export const ref = (db,path) => path;
  export const onValue = (path,callback) => {
    const send = data => callback({exists:()=>data!==null,val:()=>data});
    if(path.endsWith('/overlayConfig')) { window.emitTheme=theme=>send({theme}); send(null); }
    else if(path.endsWith('/overlay')) { window.emitOverlay=send; send(null); }
    else throw new Error('Unexpected database path');
  };
` }));

try {
  await page.goto(`${origin}/overlay.html?room=test`);
  await page.waitForFunction(() => typeof window.emitOverlay === "function");
  for (const viewport of [{ width: 3840, height: 2160 }, { width: 1920, height: 1080 }, { width: 1280, height: 720 }, { width: 320, height: 180 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    for (const theme of OVERLAY_THEMES) {
      const report = await page.evaluate(({ theme, entries }) => {
        window.emitTheme(theme);
        const failures = [];
        let minimum = Infinity;
        for (let index = 0; index < entries.length; index++) {
          window.emitOverlay({ ...entries[index], id: `${theme}-${innerWidth}-${index}`, ts: Date.now(), player: "Vareth Cal’Nyth z Ledových hor" });
          const content = document.querySelector("#content"), grid = document.querySelector("#resultGrid");
          const area = grid.getBoundingClientRect();
          const elements = [...document.querySelectorAll("#titleText, #damageText, #effectText, .player-context, #playerName, #duration")].filter(element => !element.hidden);
          const fonts = elements.map(element => parseFloat(getComputedStyle(element).fontSize));
          minimum = Math.min(minimum, ...fonts);
          const fits = content.scrollHeight <= content.clientHeight + 1 && content.scrollWidth <= content.clientWidth + 1 && grid.clientHeight > 0 && elements.every(element => element.scrollWidth <= element.clientWidth + 1);
          const bodyFits = [document.querySelector("#damageText"), document.querySelector("#effectText")].filter(element => !element.hidden).every(element => { const r = element.getBoundingClientRect(); return r.top >= area.top - 1 && r.bottom <= area.bottom + 1; });
          if (!fits || !bodyFits || Math.max(...fonts) - Math.min(...fonts) > .01) failures.push({ index, text: entries[index].effect, fonts, fits, bodyFits });
        }
        return { checked: entries.length, minimum, failures: failures.slice(0, 3), failureCount: failures.length };
      }, { theme: theme.id, entries: viewport.width === 3840 ? entries : longest });
      console.log(JSON.stringify({ viewport, theme: theme.id, ...report }));
      assert.equal(report.failureCount, 0, `${theme.id} ${viewport.width} has clipped or unequal text`);
    }
  }
  await page.setViewportSize({ width: 1920, height: 1080 });
  for (const theme of OVERLAY_THEMES) {
    await page.evaluate(theme => {
      window.emitTheme(theme);
      window.emitOverlay({ id: `screenshot-${theme}`, ts: Date.now(), title: "Dexterity – Sleight of Hand", effect: "Utrpíš 3d6 drtivého poškození. Příští tři ověření Obratnosti mají postih −3.", player: "Hea" });
    }, theme.id);
    await page.screenshot({ path: path.join(shots, `theme-${theme.id}.png`), animations: "disabled" });
    if (["parchment", "comic", "ice"].includes(theme.id)) {
      const color = await page.locator("#effectText").evaluate(e => getComputedStyle(e).color);
      assert.ok(["rgb(48, 33, 21)", "rgb(32, 28, 26)", "rgb(21, 57, 81)"].includes(color), `wrong light-theme ink: ${color}`);
    }
  }
  const fixedTime = new Date("2026-10-23T10:00:00Z");
  await page.clock.install({ time: fixedTime });
  await page.clock.pauseAt(new Date(fixedTime.getTime() + 1000));
  const emit = (id, age = 0, effect = "Utrpíš 1d6 drtivého poškození. Příští hod má postih −2.") => page.evaluate(({ id, age, effect }) => window.emitOverlay({ id, ts: Date.now() - age, title: "Útok", effect, player: "Hea" }), { id, age, effect });
  const visible = () => page.locator("#overlay-wrap").evaluate(e => e.classList.contains("visible"));
  await emit("timer-1"); await page.clock.fastForward(10000);
  await page.evaluate(() => window.emitTheme("parchment"));
  await page.clock.fastForward(9999); assert.equal(await visible(), true);
  await page.clock.fastForward(1); assert.equal(await visible(), false);
  await emit("replace-1"); await page.clock.fastForward(19000); await emit("replace-2");
  await page.clock.fastForward(2000); assert.equal(await visible(), true);
  await page.clock.fastForward(18000); assert.equal(await visible(), false);
  await emit("late", 19000); await page.clock.fastForward(999); assert.equal(await visible(), true);
  await page.clock.fastForward(1); assert.equal(await visible(), false);
  await emit("expired", 21000); assert.equal(await visible(), false);
  await emit("only-damage", 0, "Utrpíš 4d6 drtivého poškození.");
  assert.equal(await page.locator("#effectText").isVisible(), false);
  await emit("plain", 0, "Příští ověření má postih −2.");
  assert.equal(await page.locator("#damageText").isVisible(), false);
  await emit("untrusted", 0, "<img src=x onerror=alert(1)> & <script>test</script>");
  assert.equal(await page.locator("#effectText img, #effectText script").count(), 0);
  console.log("PASS exact 20-second duration, theme changes preserve deadline, event replacement, reload age, expired events, single consequences and escaped text");
  const preview = await browser.newPage();
  let firebaseRequests = 0;
  preview.on("request", request => { if (request.url().includes("firebase")) firebaseRequests++; });
  await preview.goto(`${origin}/overlay.html?preview=1&theme=ice`);
  await preview.locator("#overlay-wrap.visible").waitFor();
  assert.equal(firebaseRequests, 0);
  assert.equal(await preview.locator("#panel").getAttribute("data-theme"), "ice");
  console.log("PASS private preview has no Firebase connection or publications");
  assert.deepEqual(errors, []);
} finally { await browser.close(); await new Promise(resolve => server.close(resolve)); }
