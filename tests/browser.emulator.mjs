// Run inside the Database emulator. The browser uses the real Firebase SDK and rules.
import { chromium } from "playwright";
import { initializeTestEnvironment } from "@firebase/rules-unit-testing";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import os from "node:os";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import { discoverSeverities, selections } from "../critfail-core.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const screenshots = process.env.KRITFAILER_SCREENSHOTS || path.join(os.tmpdir(), "kritfailer-ui-review");
await fs.mkdir(screenshots, { recursive: true });
let dataText = await fs.readFile(path.join(root, "crit_fails.json"), "utf8");
const manifest = () => JSON.stringify({ version: crypto.createHash("sha256").update(dataText).digest("hex") });
const originalData = JSON.parse(dataText);
const choice = selections(originalData).find(c => c.group === "Útok");
const difficulties = discoverSeverities(originalData).filter(s => choice.severityMap[s]?.length);
assert.ok(difficulties.length);
const chosenSeverity = difficulties.includes("Vážný") ? "Vážný" : difficulties[0];
const env = await initializeTestEnvironment({ projectId: "demo-kritfailer", database: { host: "127.0.0.1", port: 9000, rules: await fs.readFile(path.join(root, "database.rules.json"), "utf8") } });
await env.clearDatabase();
const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url, "http://localhost");
    if (url.pathname === "/crit_fails.meta.json") { response.setHeader("Content-Type", "application/json"); response.end(manifest()); return; }
    if (url.pathname === "/crit_fails.json") { response.setHeader("Content-Type", "application/json"); response.end(dataText); return; }
    const filename = path.resolve(root, "." + decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname));
    if (!filename.startsWith(root)) { response.writeHead(403).end(); return; }
    response.setHeader("Content-Type", ({ ".js": "text/javascript", ".mjs": "text/javascript", ".html": "text/html", ".json": "application/json", ".png": "image/png" })[path.extname(filename)] || "text/plain");
    response.end(await fs.readFile(filename));
  } catch { response.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ ...(process.env.KRITFAILER_CHROMIUM_EXECUTABLE ? { executablePath: process.env.KRITFAILER_CHROMIUM_EXECUTABLE } : { channel: "chromium" }), headless: true, args: ["--no-sandbox", ...JSON.parse(process.env.KRITFAILER_CHROMIUM_ARGS || "[]")] });
const errors = [];
async function pageFor(uid, width = 1440) {
  const context = await browser.newContext({ viewport: { width, height: 1000 } });
  await context.route("https://www.gstatic.com/firebasejs/10.7.1/*", route => route.fulfill({ path: path.join(root, "node_modules/firebase", new URL(route.request().url()).pathname.split("/").at(-1)), contentType: "text/javascript" }));
  await context.route("**/firebase-client.mjs", route => route.fulfill({ contentType: "text/javascript", body: `
    import {initializeApp} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
    import {getDatabase,connectDatabaseEmulator} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";
    export {ref,set,get,update,remove,onValue,push,onDisconnect,runTransaction,serverTimestamp,query,orderByChild,limitToLast} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";
    export async function connectFirebase(){const app=initializeApp({projectId:"demo-kritfailer",databaseURL:"https://demo-kritfailer.firebaseio.com"});const db=getDatabase(app);connectDatabaseEmulator(db,"127.0.0.1",9000,{mockUserToken:{sub:${JSON.stringify(uid)},user_id:${JSON.stringify(uid)}}});return {db,uid:${JSON.stringify(uid)}};}
  ` }));
  const page = await context.newPage(); page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (message.type() === "error" || message.type() === "warning") console.log(`BROWSER ${uid}: ${message.text()}`); });
  page.on("dialog", dialog => dialog.accept());
  return page;
}
async function waitText(page, selector, expected) {
  await page.waitForFunction(({ selector, expected }) => document.querySelector(selector)?.textContent.includes(expected), { selector, expected }, { timeout: 15000 });
}
async function records() {
  let value;
  await env.withSecurityRulesDisabled(async c => { value = (await c.database().ref("roomsV2").get()).val(); });
  return value;
}

try {
  const dm = await pageFor("browser-dm"), player = await pageFor("browser-player"), second = await pageFor("browser-second");
  await dm.goto(origin); await dm.locator("#setup").waitFor({ state: "visible" });
  await dm.locator("#nameInput").fill("Ondra – DM"); await dm.getByRole("button", { name: "👑 Vytvořit místnost", exact: true }).click();
  await dm.locator("#roomInput").fill("Kroniky Khanu"); await dm.getByRole("button", { name: "✅ Vytvořit", exact: true }).click();
  await dm.locator("#dmPanel").waitFor({ state: "visible" });
  await player.goto(origin); await player.locator("#setup").waitFor({ state: "visible" });
  await player.locator("#nameInput").fill("Borin"); await player.getByRole("button", { name: "Připojit", exact: true }).click();
  await player.locator("#playerPanel").waitFor({ state: "visible" });
  const playerButton = player.locator("#playerGenerator [data-choice]").filter({ hasText: choice.title }).first();
  assert.equal(await playerButton.isDisabled(), true);
  assert.equal(await player.locator("#severityBtns").isVisible(), false);
  await dm.locator("#severityBtns").getByRole("button", { name: chosenSeverity, exact: true }).click();
  await waitText(player, "#playerSeverity", chosenSeverity);
  await playerButton.click();
  await waitText(dm, "#resHeader", "Borin"); await player.locator("#playerResult .res-effect").waitFor();
  assert.equal(await dm.locator("#resBody .res-effect").textContent(), await player.locator("#playerResult .res-effect").textContent());
  const roomId = Object.keys(await records())[0];
  const overlay = await pageFor("browser-overlay"); await overlay.goto(`${origin}/overlay.html?room=${roomId}`);
  await waitText(overlay, "#playerName", "Borin");
  assert.equal((await dm.locator("#resBody .res-effect").textContent()).replace(/^⚠️ /, ""), await overlay.locator("#effectText").textContent());
  console.log("PASS player generation, DM/player agreement, room difficulty, overlay");

  await second.goto(origin); await second.locator("#setup").waitFor({ state: "visible" });
  await second.locator("#nameInput").fill("Benet"); await second.getByRole("button", { name: "Připojit", exact: true }).click();
  await second.locator("#playerPanel").waitFor({ state: "visible" }); await waitText(second, "#playerSeverity", chosenSeverity);
  await Promise.all([playerButton.click(), second.locator("#playerGenerator [data-choice]").filter({ hasText: choice.title }).first().click()]);
  await dm.waitForFunction(() => document.querySelectorAll("#dmHistory button").length >= 3);
  const all = await records();
  assert.equal(Object.keys(all[roomId].results["browser-player"]).length, 2);
  assert.equal(Object.keys(all[roomId].results["browser-second"]).length, 1);
  console.log("PASS concurrent players retain distinct shared results");

  if (difficulties.length > 1) {
    const next = difficulties.find(s => s !== chosenSeverity);
    await dm.locator("#severityBtns").getByRole("button", { name: next, exact: true }).click();
    await waitText(player, "#playerSeverity", next); await playerButton.click();
    await waitText(dm, "#resHeader", `Borin · ${choice.label} / ${next}`);
    console.log("PASS live DM difficulty change");
  }
  await dm.locator("#generator [data-choice]").filter({ hasText: choice.title }).first().click();
  await waitText(dm, "#resHeader", "Ondra – DM");
  await dm.reload();
  try { await dm.locator("#dmPanel").waitFor({ state: "visible", timeout: 10000 }); }
  catch (error) {
    console.log("RESTORE_STATE", await dm.evaluate(() => ({ saved: localStorage.getItem("kf_state_v2:browser-dm"), loading: document.querySelector("#loading").textContent, setup: document.querySelector("#setup").className })));
    throw error;
  }
  assert.equal((await records())[roomId].dm, "browser-dm");
  console.log("PASS DM generation and persistent room ownership after reload");

  await dm.locator("#targets .target-row").filter({ hasText: "Borin" }).getByRole("button", { name: "📦 Oba", exact: true }).click();
  await waitText(dm, "#resHeader", "Borin");
  await player.waitForFunction(expected => document.querySelector("#playerResult .res-effect")?.textContent === expected, await dm.locator("#resBody .res-effect").textContent());
  console.log("PASS DM can manually send the selected result to a player");

  await dm.screenshot({ path: path.join(screenshots, "dm-desktop.png"), animations: "disabled" });
  await player.evaluate(() => window.scrollTo(0, 0));
  await player.screenshot({ path: path.join(screenshots, "player-desktop.png"), animations: "disabled" });
  await overlay.screenshot({ path: path.join(screenshots, "overlay.png"), animations: "disabled" });
  await player.setViewportSize({ width: 390, height: 844 });
  await player.screenshot({ path: path.join(screenshots, "player-mobile.png"), animations: "disabled" });
  assert.equal(await player.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  assert.equal(await dm.evaluate(() => getComputedStyle(document.body).backgroundColor), "rgb(26, 26, 46)");
  console.log("PASS original theme colours and mobile layout");

  const changed = structuredClone(originalData);
  for (const choice of selections(changed)) for (const pool of Object.values(choice.severityMap)) for (const entry of pool) entry.effect = "Nový obsah z Excelu";
  dataText = JSON.stringify(changed);
  await dm.bringToFront(); await dm.evaluate(() => document.dispatchEvent(new Event("visibilitychange")));
  await waitText(dm, "#notif", "aktualizovány");
  await dm.locator("#generator [data-choice]").filter({ hasText: choice.title }).first().click();
  await waitText(dm, "#resBody", "Nový obsah z Excelu");
  console.log("PASS updated dataset is loaded without reloading the application");

  await dm.locator("#dmPlayerList .player-chip").filter({ hasText: "Borin" }).getByRole("button", { name: "❌ Kick" }).click();
  await player.locator("#setup").waitFor({ state: "visible" });
  assert.equal((await records())[roomId].players["browser-player"], undefined);
  await player.evaluate(() => document.dispatchEvent(new Event("visibilitychange")));
  assert.equal((await records())[roomId].players["browser-player"], undefined);
  console.log("PASS kicked player is not silently reconnected");
  assert.deepEqual(errors, []);
  console.log(`SCREENSHOTS ${screenshots}`);
} finally {
  await browser.close(); await new Promise(resolve => server.close(resolve)); await env.cleanup();
}
