import { before, after, beforeEach, test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { initializeTestEnvironment, assertFails, assertSucceeds } from "@firebase/rules-unit-testing";

let env;
const stamp = { ".sv": "timestamp" }, hash = "a".repeat(64);
const database = uid => env.authenticatedContext(uid).database();
const base = { dm: "dm", name: "Test", passwordHash: "", createdAt: 1, settings: { severity: "Vážný", revision: 1, updatedBy: "dm", updatedAt: 1 }, players: { dm: { name: "DM", joinedAt: 1, joinProof: "" }, p1: { name: "Ondra", joinedAt: 1, joinProof: "" }, p2: { name: "Péťa", joinedAt: 1, joinProof: "" } } };
const lobby = { name: "Test", dmUid: "dm", locked: false, createdAt: 1, playerCount: 3, dmOnline: true };

before(async () => { env = await initializeTestEnvironment({ projectId: "demo-kritfailer", database: { host: "127.0.0.1", port: 9000, rules: await fs.readFile(new URL("../database.rules.json", import.meta.url), "utf8") } }); });
after(async () => { await env?.cleanup(); });
beforeEach(async () => { await env.clearDatabase(); await env.withSecurityRulesDisabled(async context => context.database().ref().set({ roomsV2: { room: structuredClone(base) }, lobbyV2: { room: lobby } })); });

function event(uid = "p1", extra = {}) {
  return { entryId: "attack:Melee|Vážný|0", label: "Útok – Melee", severity: "Vážný", settingsRevision: 1, effect: "Ztratíš reakci.", roleplay: ["RP1", "RP2"], actorId: uid, actorName: uid === "p1" ? "Ondra" : uid === "p2" ? "Péťa" : "DM", targetId: uid, targetName: uid === "p1" ? "Ondra" : uid === "p2" ? "Péťa" : "DM", datasetVersion: hash, kind: "roll", clientTs: Date.now(), ts: stamp, ...extra };
}
function publish(uid, id, value = event(uid)) {
  return database(uid).ref().update({ [`roomsV2/room/results/${value.targetId}/${id}`]: value, "roomsV2/room/overlay": { ...value, id, title: value.label, player: value.targetName } });
}
function difficulty(severity, revision) { return { severity, revision, updatedBy: "dm", updatedAt: stamp }; }

test("DM creates a room and its public lobby atomically", async () => {
  const room = { ...structuredClone(base), createdAt: stamp, settings: { severity: "", revision: 0, updatedBy: "dm", updatedAt: stamp }, players: { dm: { name: "DM", joinedAt: stamp, joinProof: "" } } };
  await assertSucceeds(database("dm").ref().update({ "roomsV2/new": room, "lobbyV2/new": { ...lobby, playerCount: 1, createdAt: stamp } }));
});
test("only DM can change the room difficulty", async () => {
  await assertFails(database("p1").ref("roomsV2/room/settings").set(difficulty("Sranda", 2)));
  await assertSucceeds(database("dm").ref("roomsV2/room/settings").set(difficulty("Sranda", 2)));
});
test("only DM can choose a supported overlay theme, readable by the TV", async () => {
  const config = "roomsV2/room/overlayConfig";
  await assertFails(database("p1").ref(config).set({ theme: "ice" }));
  await assertFails(database("visitor").ref(config).set({ theme: "ice" }));
  await assertFails(database("dm").ref(config).set({ theme: "unknown" }));
  await assertFails(database("dm").ref(config).set({ theme: "ice", severity: "Vážný" }));
  for (const theme of ["grimoire", "inferno", "astral", "parchment", "nordic", "comic", "ice"]) {
    await assertSucceeds(database("dm").ref(config).set({ theme }));
    assert.deepEqual((await assertSucceeds(database("visitor").ref(config).get())).val(), { theme });
  }
  assert.equal((await database("dm").ref("roomsV2/room/settings/revision").get()).val(), 1);
});
test("player result is shared with its player, DM and overlay", async () => {
  await assertSucceeds(publish("p1", "one"));
  const own = await assertSucceeds(database("p1").ref("roomsV2/room/results/p1/one").get());
  const dm = await assertSucceeds(database("dm").ref("roomsV2/room/results/p1/one").get());
  assert.deepEqual(own.val(), dm.val());
  const overlay = await assertSucceeds(database("visitor").ref("roomsV2/room/overlay").get());
  assert.equal(overlay.val().effect, own.val().effect);
});
test("other players cannot read a player's private result", async () => {
  await publish("p1", "one");
  await assertFails(database("p2").ref("roomsV2/room/results/p1").get());
});
test("player cannot generate for another player or impersonate DM", async () => {
  await assertFails(publish("p1", "wrong", event("p1", { targetId: "p2", targetName: "Péťa" })));
  await assertFails(publish("p1", "wrong", event("p1", { actorId: "dm", actorName: "DM" })));
  await assertFails(publish("p1", "wrong", event("p1", { kind: "assignment" })));
});
test("stale difficulty revision rejects the complete result and overlay write", async () => {
  await database("dm").ref("roomsV2/room/settings").set(difficulty("Sranda", 2));
  await assertFails(publish("p1", "stale"));
  assert.equal((await database("dm").ref("roomsV2/room/results").get()).exists(), false);
});
test("changing severity without changing its revision is rejected", async () => {
  await assertFails(publish("p1", "wrong", event("p1", { severity: "Sranda" })));
});
test("two players retain both concurrent results", async () => {
  await Promise.all([assertSucceeds(publish("p1", "one")), assertSucceeds(publish("p2", "two"))]);
  const snapshot = await database("dm").ref("roomsV2/room/results").get();
  assert.equal(snapshot.child("p1/one").exists(), true); assert.equal(snapshot.child("p2/two").exists(), true);
});
test("results are immutable for their player", async () => {
  await publish("p1", "one");
  await assertFails(database("p1").ref("roomsV2/room/results/p1/one/effect").set("different"));
});
test("DM can also generate and assign a result to a player", async () => {
  await assertSucceeds(publish("dm", "dm-roll"));
  await assertSucceeds(publish("dm", "assignment", event("dm", { targetId: "p1", targetName: "Ondra", kind: "assignment" })));
});
test("only the original DM owns the room, including after reconnect", async () => {
  await assertFails(database("p1").ref("roomsV2/room/dm").set("p1"));
  await assertFails(database("old-dm").ref("roomsV2/room/dm").set("old-dm"));
  await assertFails(database("dm").ref("roomsV2/room/dm").set("p1"));
});
test("kicked player cannot recreate membership or publish another result", async () => {
  await database("dm").ref().update({ "roomsV2/room/banned/p1": true, "roomsV2/room/players/p1": null, "roomsV2/room/presence/p1": null });
  await assertFails(database("p1").ref("roomsV2/room/players/p1").set({ name: "Ondra", joinedAt: stamp, joinProof: "" }));
  await assertFails(publish("p1", "after-kick"));
});
test("password proof is required for a new membership and hidden from lobby", async () => {
  await env.withSecurityRulesDisabled(context => context.database().ref("roomsV2/room/passwordHash").set(hash));
  await assertFails(database("new-player").ref("roomsV2/room/players/new-player").set({ name: "New", joinedAt: stamp, joinProof: "" }));
  await assertSucceeds(database("new-player").ref("roomsV2/room/players/new-player").set({ name: "New", joinedAt: stamp, joinProof: hash }));
  await assertFails(database("visitor").ref("roomsV2/room/passwordHash").get());
  assert.equal(JSON.stringify((await database("visitor").ref("lobbyV2").get()).val()).includes(hash), false);
});
test("only DM can remove a room", async () => {
  await assertFails(database("p1").ref("roomsV2/room").remove());
  await assertSucceeds(database("dm").ref().update({ "roomsV2/room": null, "lobbyV2/room": null }));
});
