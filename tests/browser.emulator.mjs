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
import { OVERLAY_THEMES, splitOverlayEffect } from "../overlay-themes.mjs";

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
async function waitReady(page) {
  await page.waitForFunction(() => !document.querySelector("#playerGenerator [data-choice]")?.disabled);
}
async function assertHiddenDifficulty(page) {
  assert.equal(await page.locator("#playerSeverity").count(), 0);
  for (const selector of ["#playerResult .result-context", "#playerHistory"]) {
    const text = await page.locator(selector).textContent() || "";
    for (const severity of difficulties) assert.equal(text.includes(severity), false);
  }
  const labels = await page.locator("#playerGenerator [data-choice]").evaluateAll(buttons => buttons.map(button => button.title).join(" "));
  for (const severity of difficulties) assert.equal(labels.includes(severity), false);
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
  await waitReady(player);
  await playerButton.click();
  await waitText(dm, "#resHeader", "Borin"); await player.locator("#playerResult .res-effect").waitFor();
  assert.equal(await dm.locator("#resBody .res-effect").textContent(), await player.locator("#playerResult .res-effect").textContent());
  await assertHiddenDifficulty(player);
  assert.equal(await player.locator("#playerResult .res-rp").count(), 1);
  assert.equal(await player.locator("#playerResult .rp-label").textContent(), "🎭 Roleplay");
  const roomId = Object.keys(await records())[0];
  const overlay = await pageFor("browser-overlay"); await overlay.goto(`${origin}/overlay.html?room=${roomId}`);
  await waitText(overlay, "#playerName", "Borin");
  const firstEffect = (await dm.locator("#resBody .res-effect").textContent()).replace(/^⚠️ /, "");
  const firstParts = splitOverlayEffect(firstEffect);
  assert.equal(await overlay.locator("#damageText").textContent(), firstParts.damage);
  assert.equal(await overlay.locator("#effectText").textContent(), firstParts.consequence);
  assert.equal(await overlay.locator("#sevBadge").count(), 0);
  assert.equal(await overlay.locator("#panel").getAttribute("data-theme"), "grimoire");
  console.log("PASS shared player result with one roleplay and hidden difficulty in player view and overlay");

  assert.equal(await player.locator("#overlaySettings").isVisible(), false);
  await dm.locator("#overlaySettings summary").click();
  const beforeTheme = structuredClone((await records())[roomId]);
  for (const theme of OVERLAY_THEMES) {
    await dm.locator(`[data-overlay-theme="${theme.id}"]`).click();
    await overlay.waitForFunction(id => document.querySelector("#panel").dataset.theme === id, theme.id);
    await dm.waitForFunction(id => document.querySelector(`[data-overlay-theme="${id}"]`)?.getAttribute("aria-pressed") === "true", theme.id);
    assert.ok((await dm.locator("#overlayPreview").getAttribute("src")).includes(`theme=${theme.id}`));
  }
  const afterTheme = (await records())[roomId];
  assert.deepEqual(afterTheme.results, beforeTheme.results);
  assert.deepEqual(afterTheme.overlay, beforeTheme.overlay);
  assert.deepEqual(afterTheme.settings, beforeTheme.settings);
  assert.equal(afterTheme.overlayConfig.theme, "ice");
  await overlay.reload();
  await overlay.waitForFunction(() => document.querySelector("#panel").dataset.theme === "ice");
  console.log("PASS all seven themes switch the open TV, persist after reload and leave results and difficulty unchanged");

  await second.goto(origin); await second.locator("#setup").waitFor({ state: "visible" });
  await second.locator("#nameInput").fill("Benet"); await second.getByRole("button", { name: "Připojit", exact: true }).click();
  await second.locator("#playerPanel").waitFor({ state: "visible" }); await waitReady(second);
  await Promise.all([playerButton.click(), second.locator("#playerGenerator [data-choice]").filter({ hasText: choice.title }).first().click()]);
  await dm.waitForFunction(() => document.querySelectorAll("#dmHistory button").length >= 3);
  const all = await records();
  assert.equal(Object.keys(all[roomId].results["browser-player"]).length, 2);
  assert.equal(Object.keys(all[roomId].results["browser-second"]).length, 1);
  console.log("PASS concurrent players retain distinct shared results");

  if (difficulties.length > 1) {
    const next = difficulties.find(s => s !== chosenSeverity);
    await dm.locator("#severityBtns").getByRole("button", { name: next, exact: true }).click();
    await waitText(dm, "#sevLabel", next); await waitReady(player);
    await playerButton.click();
    await waitText(dm, "#resHeader", `Borin · ${choice.label} / ${next}`);
    await assertHiddenDifficulty(player);
    console.log("PASS live DM difficulty change remains hidden from players");
  }
  const beforeDraft = (await records())[roomId];
  const playerBeforeDraft = await player.locator("#playerResult").textContent();
  const secondBeforeDraft = await second.locator("#playerResult").textContent();
  const historyBeforeDraft = await dm.locator("#dmHistory button").count();
  await dm.locator("#generator [data-choice]").filter({ hasText: choice.title }).first().click();
  await waitText(dm, "#resHeader", "Náhled pro DM:");
  const draftEffect = await dm.locator("#resBody .res-effect").textContent();
  const draftRoleplay = await dm.locator("#resBody .res-rp .preserve-lines").textContent();
  assert.equal(await dm.locator("#resBody .res-rp").count(), 1);
  assert.deepEqual((await records())[roomId].results, beforeDraft.results);
  assert.deepEqual((await records())[roomId].overlay, beforeDraft.overlay);
  assert.equal(await player.locator("#playerResult").textContent(), playerBeforeDraft);
  assert.equal(await second.locator("#playerResult").textContent(), secondBeforeDraft);
  console.log("PASS DM preview stays private without publishing any result or overlay");

  await playerButton.click();
  await dm.waitForFunction(count => document.querySelectorAll("#dmHistory button").length > count, historyBeforeDraft);
  assert.ok((await dm.locator("#resHeader").textContent()).includes("Náhled pro DM:"));
  assert.equal(await dm.locator("#resBody .res-effect").textContent(), draftEffect);
  console.log("PASS a concurrent player roll cannot overwrite the DM preview");

  const beforeSend = (await records())[roomId];
  await dm.locator("#targets .target-row").filter({ hasText: "Borin" }).getByRole("button", { name: "📨 Poslat výsledek", exact: true }).click();
  await waitText(dm, "#resHeader", "Borin");
  await player.waitForFunction(expected => document.querySelector("#playerResult .res-effect")?.textContent === expected, draftEffect);
  await player.waitForFunction(expected => document.querySelector("#playerResult .res-rp .preserve-lines")?.textContent === expected, draftRoleplay);
  const sentRoom = (await records())[roomId];
  assert.equal(Object.keys(sentRoom.results["browser-player"]).length, Object.keys(beforeSend.results["browser-player"]).length + 1);
  assert.deepEqual(sentRoom.results["browser-second"], beforeSend.results["browser-second"]);
  assert.equal(sentRoom.overlay.targetId, "browser-player");
  assert.equal(sentRoom.overlay.effect, draftEffect.replace(/^⚠️ /, ""));
  assert.equal(sentRoom.overlay.roleplay.length, 1);
  assert.equal(await second.locator("#playerResult").textContent(), secondBeforeDraft);
  await assertHiddenDifficulty(player);
  console.log("PASS DM sends the exact preview and one roleplay only to the selected player");

  await dm.reload();
  await dm.waitForFunction(() => document.querySelector("#overlayThemeLabel").textContent === "Ledové království");
  try { await dm.locator("#dmPanel").waitFor({ state: "visible", timeout: 10000 }); }
  catch (error) {
    console.log("RESTORE_STATE", await dm.evaluate(() => ({ saved: localStorage.getItem("kf_state_v2:browser-dm"), loading: document.querySelector("#loading").textContent, setup: document.querySelector("#setup").className })));
    throw error;
  }
  assert.equal((await records())[roomId].dm, "browser-dm");
  console.log("PASS persistent room ownership and sent result after reload");

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
