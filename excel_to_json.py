import pandas as pd
import json

EXCEL_FILE = "crit_fails.xlsx"
OUTPUT_JSON = "crit_fails.json"

ALL_SEVERITIES = ["Lehký", "Střední", "Těžký", "Sranda"]

def normalize_severity(s):
    if not s:
        return "Lehký"
    s = str(s).strip().lower()
    if "leh" in s:
        return "Lehký"
    if "stř" in s or "str" in s:
        return "Střední"
    if "těž" in s or "tez" in s:
        return "Těžký"
    if "sranda" in s:
        return "Sranda"
    return "Lehký"


def ensure_all_severities(container):
    for sev in ALL_SEVERITIES:
        container.setdefault(sev, [])


def build_json_from_excel():
    xls = pd.ExcelFile(EXCEL_FILE)
    data = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        action = sheet.strip()
        data[action] = {}

        for _, row in df.iterrows():

            skill = str(row.get("skill", "")).strip()
            attribute = str(row.get("skill_category", "")).strip()
            attack_type = str(row.get("attack_type", "")).strip()
            severity = normalize_severity(row.get("severity", ""))

            effect = str(row.get("effect", "")).strip()
            roleplay_1 = str(row.get("roleplay_1", "")).strip()
            roleplay_2 = str(row.get("roleplay_2", "")).strip()

            if not effect:
                continue

            entry = {
                "effect": effect,
                "roleplay": [roleplay_1, roleplay_2],
                "weight": int(row.get("weight", 1)) if not pd.isna(row.get("weight")) else 1
            }

            # =========================
            # ÚTOK
            # =========================
            if action == "Útok":
                if not attack_type:
                    attack_type = "Melee"

                data[action].setdefault(attack_type, {})
                ensure_all_severities(data[action][attack_type])
                data[action][attack_type][severity].append(entry)

            # =========================
            # SKILL
            # =========================
            elif action == "Skill":
                if not attribute or not skill:
                    continue

                data[action].setdefault(attribute, {})
                data[action][attribute].setdefault(skill, {})
                ensure_all_severities(data[action][attribute][skill])
                data[action][attribute][skill][severity].append(entry)

            # =========================
            # OBRANA / OSTATNÍ
            # =========================
            else:
                ensure_all_severities(data[action])
                data[action][severity].append(entry)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ JSON má všechny severity")


if __name__ == "__main__":
    build_json_from_excel()<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>KritFailer</title>

<style>
body { margin:0; font-family:Arial; background:#0e0e0e; color:white; }

header {
  display:flex;
  justify-content:space-between;
  padding:10px;
  background:#1a1a1a;
}

.title { color:#ff9800; font-weight:bold; }

.container { padding:12px; }

button {
  margin:4px;
  padding:8px 12px;
  border:none;
  border-radius:8px;
  background:#222;
  color:white;
  cursor:pointer;
}

button:hover { background:#444; }

.active { background:#ff9800 !important; }

.card {
  background:#1a1a1a;
  padding:10px;
  margin-top:5px;
  border-radius:10px;
}

input {
  padding:10px;
  margin:5px;
  border:none;
  border-radius:8px;
}

.room {
  padding:8px;
  margin:5px;
  background:#1a1a1a;
  border-radius:8px;
}

.meta {
  color:#aaa;
  font-size:12px;
  margin-bottom:6px;
}
</style>
</head>

<body>

<header>
  <div class="title">🎲 KritFailer</div>
  <div id="playersTop"></div>
  <div id="topButtons"></div>
</header>

<div id="setup" class="container">

  <input id="name" placeholder="Jméno"><br>
  <input id="room" placeholder="Room"><br>

  <button onclick="joinDM()">👑 DM</button>
  <button onclick="joinPlayer()">🎭 Hráč</button>

  <h3>Otevřené hry</h3>
  <div id="roomsList"></div>

</div>

<div id="app" class="container" style="display:none;">

  <div id="dmPanel" style="display:none;">

    <div id="severityButtons"></div>

    <h3>Akce</h3>
    <button onclick="generateAttack('Melee', this)">⚔️ Melee</button>
    <button onclick="generateAttack('Ranged', this)">🏹 Ranged</button>
    <button onclick="generateDefense(this)">🛡️ Obrana</button>

    <h3>🎲 Skilly</h3>
    <div id="skills"></div>

  </div>

  <div id="playerPanel" style="display:none;">
    <h3 id="roomName"></h3>
    <div id="playerResult">Čekám na výsledek...</div>
  </div>

</div>

<script type="module">

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getDatabase, ref, set, onValue, get, remove, onDisconnect } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyDI3qi2zqosghoQNRQ31hDZU1y_tBioedY",
  databaseURL: "https://ktit-fail-generator-default-rtdb.europe-west1.firebasedatabase.app"
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// ===== STATE =====
let room="", name="", myId="", isDM=false;
let players={}, data={};
let severityList=[], severity="";

// ===== SESSION =====
if(localStorage.room){
  room = localStorage.room;
  name = localStorage.name;
  myId = localStorage.myId;
  isDM = localStorage.isDM==="true";
  start();
}

// ===== LOAD JSON =====
fetch("crit_fails.json").then(r=>r.json()).then(j=>{
  data=j;
  buildSeverity();
  buildSkills();
});

// ===== SEVERITY SYSTEM =====
function buildSeverity(){

  const set = new Set();

  if(data["Útok"]){
    Object.values(data["Útok"]).forEach(type=>{
      Object.keys(type).forEach(sev=> set.add(sev));
    });
  }

  if(data["Obrana"]){
    Object.keys(data["Obrana"]).forEach(sev=> set.add(sev));
  }

  if(data["Skill"]){
    Object.values(data["Skill"]).forEach(attr=>{
      Object.values(attr).forEach(skill=>{
        Object.keys(skill).forEach(sev=> set.add(sev));
      });
    });
  }

  severityList = Array.from(set);

  severity = severityList[0];

  renderSeverityButtons();
}

function renderSeverityButtons(){

  const container = document.getElementById("severityButtons");

  let html = "";

  severityList.forEach(sev=>{
    html += `<button id="sev-${sev}" onclick="setSeverity('${sev}')">${sev}</button>`;
  });

  container.innerHTML = html;

  setSeverity(severity);
}

function setSeverity(level){
  severity = level;

  document.querySelectorAll("#severityButtons button").forEach(b=>{
    b.classList.remove("active");
  });

  const btn = document.getElementById("sev-"+level);
  if(btn) btn.classList.add("active");
}
window.setSeverity = setSeverity;

// ===== LOBBY =====
function quickJoin(r){
  document.getElementById("room").value = r;
}
window.quickJoin = quickJoin;

onValue(ref(db,"rooms"), snap=>{
  const rooms = snap.val() || {};
  let html="";
  Object.keys(rooms).forEach(r=>{
    html += `<div class="room">${r} <button onclick="quickJoin('${r}')">Join</button></div>`;
  });
  document.getElementById("roomsList").innerHTML = html;
});

// ===== LOGIN =====
async function joinDM(){

  room = val("room");
  name = val("name");
  isDM = true;

  const snap = await get(ref(db,"rooms/"+room+"/players"));
  const p = snap.val();

  if(p && Object.values(p).some(x=>x.name.includes("👑"))){
    alert("DM už existuje");
    return;
  }

  myId = "DM_"+Date.now();

  await set(ref(db,"rooms/"+room+"/players/"+myId),{ name:name+" 👑" });

  save();
  start();
}
window.joinDM = joinDM;

async function joinPlayer(){

  room = val("room");
  name = val("name");

  const snap = await get(ref(db,"rooms/"+room));

  if(!snap.exists()){
    alert("Room neexistuje");
    return;
  }

  const playersSnap = await get(ref(db,"rooms/"+room+"/players"));
  const p = playersSnap.val() || {};

  const existing = Object.entries(p).find(([id,x])=>x.name===name);

  if(existing){
    myId = existing[0];
  } else {
    myId = "P_"+Date.now();
    await set(ref(db,"rooms/"+room+"/players/"+myId),{ name });
  }

  save();
  start();
}
window.joinPlayer = joinPlayer;

// ===== START =====
function start(){

  document.getElementById("setup").style.display="none";
  document.getElementById("app").style.display="block";

  if(isDM){
    document.getElementById("dmPanel").style.display="block";
    document.getElementById("topButtons").innerHTML =
      `<button onclick="deleteRoom()">🗑️</button><button onclick="logout()">Logout</button>`;
  } else {
    document.getElementById("playerPanel").style.display="block";
    document.getElementById("roomName").innerText="Room: "+room;
    document.getElementById("topButtons").innerHTML =
      `<button onclick="logout()">Logout</button>`;
  }

  onDisconnect(ref(db,"rooms/"+room+"/players/"+myId)).remove();

  listenPlayers();
  listenRoom();
  listenMessages();
}

// ===== PLAYERS =====
function listenPlayers(){
  onValue(ref(db,"rooms/"+room+"/players"), snap=>{
    players = snap.val() || {};
    document.getElementById("playersTop").innerText =
      Object.values(players).map(p=>p.name).join(" | ");
  });
}

// ===== ROOM DELETE =====
function listenRoom(){
  onValue(ref(db,"rooms/"+room), snap=>{
    if(!snap.exists()){
      logout();
    }
  });
}

// ===== GENERATE =====
function generateSkill(attr, skill, btn){
  const pool = data.Skill?.[attr]?.[skill]?.[severity] || [];
  render(btn, pool, `Skill (${skill})`);
}
window.generateSkill = generateSkill;

function generateAttack(type, btn){
  const pool = data["Útok"]?.[type]?.[severity] || [];
  render(btn, pool, `Útok (${type})`);
}
window.generateAttack = generateAttack;

function generateDefense(btn){
  const pool = data["Obrana"]?.[severity] || [];
  render(btn, pool, "Obrana");
}
window.generateDefense = generateDefense;

// ===== RENDER =====
function render(btn, pool, label){

  document.querySelectorAll(".card").forEach(e=>e.remove());

  if(!pool || pool.length === 0){
    alert("Žádná data pro tuto obtížnost");
    return;
  }

  const r = pool[Math.floor(Math.random()*pool.length)];

  let playersHTML="";

  Object.entries(players).forEach(([id,p])=>{
    if(!p.name.includes("👑")){
      playersHTML += `<button onclick="send('${id}','${r.effect}')">${p.name}</button>`;
    }
  });

  const div=document.createElement("div");
  div.className="card";

  div.innerHTML=`
    <div class="meta">${severity} | ${label}</div>
    <b>${r.effect}</b><br>
    ${r.roleplay.join("<br>")}<br><br>
    ${playersHTML}
  `;

  btn.after(div);
}

// ===== SEND =====
function send(pid,text){
  set(ref(db,"rooms/"+room+"/msg/"+pid), text);
}
window.send = send;

// ===== RECEIVE =====
function listenMessages(){
  onValue(ref(db,"rooms/"+room+"/msg/"+myId), snap=>{
    if(snap.val()){
      document.getElementById("playerResult").innerText = snap.val();
    }
  });
}

// ===== DELETE =====
function deleteRoom(){
  remove(ref(db,"rooms/"+room));
}
window.deleteRoom = deleteRoom;

// ===== LOGOUT =====
function logout(){
  localStorage.clear();
  location.reload();
}
window.logout = logout;

// ===== HELPERS =====
function val(id){ return document.getElementById(id).value; }

function save(){
  localStorage.room=room;
  localStorage.name=name;
  localStorage.myId=myId;
  localStorage.isDM=isDM;
}

// ===== SKILLS =====
function buildSkills(){

  let html="";

  Object.entries(data.Skill).forEach(([attr,skills])=>{
    html+=`<h4>${attr}</h4>`;
    Object.keys(skills).forEach(s=>{
      html+=`<button onclick="generateSkill('${attr}','${s}', this)">${s}</button>`;
    });
  });

  document.getElementById("skills").innerHTML=html;
}

</script>

</body>
</html><!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>KritFailer</title>

<style>
body { margin:0; font-family:Arial; background:#0e0e0e; color:white; }

header {
  display:flex;
  justify-content:space-between;
  padding:10px;
  background:#1a1a1a;
}

.title { color:#ff9800; font-weight:bold; }

.container { padding:12px; }

button {
  margin:4px;
  padding:8px 12px;
  border:none;
  border-radius:8px;
  background:#222;
  color:white;
  cursor:pointer;
}

button:hover { background:#444; }

.active { background:#ff9800 !important; }

.card {
  background:#1a1a1a;
  padding:10px;
  margin-top:5px;
  border-radius:10px;
}

input {
  padding:10px;
  margin:5px;
  border:none;
  border-radius:8px;
}

.room {
  padding:8px;
  margin:5px;
  background:#1a1a1a;
  border-radius:8px;
}

.meta {
  color:#aaa;
  font-size:12px;
  margin-bottom:6px;
}
</style>
</head>

<body>

<header>
  <div class="title">🎲 KritFailer</div>
  <div id="playersTop"></div>
  <div id="topButtons"></div>
</header>

<div id="setup" class="container">

  <input id="name" placeholder="Jméno"><br>
  <input id="room" placeholder="Room"><br>

  <button onclick="joinDM()">👑 DM</button>
  <button onclick="joinPlayer()">🎭 Hráč</button>

  <h3>Otevřené hry</h3>
  <div id="roomsList"></div>

</div>

<div id="app" class="container" style="display:none;">

  <div id="dmPanel" style="display:none;">

    <div id="severityButtons"></div>

    <h3>Akce</h3>
    <button onclick="generateAttack('Melee', this)">⚔️ Melee</button>
    <button onclick="generateAttack('Ranged', this)">🏹 Ranged</button>
    <button onclick="generateDefense(this)">🛡️ Obrana</button>

    <h3>🎲 Skilly</h3>
    <div id="skills"></div>

  </div>

  <div id="playerPanel" style="display:none;">
    <h3 id="roomName"></h3>
    <div id="playerResult">Čekám na výsledek...</div>
  </div>

</div>

<script type="module">

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getDatabase, ref, set, onValue, get, remove, onDisconnect } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyDI3qi2zqosghoQNRQ31hDZU1y_tBioedY",
  databaseURL: "https://ktit-fail-generator-default-rtdb.europe-west1.firebasedatabase.app"
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// ===== STATE =====
let room="", name="", myId="", isDM=false;
let players={}, data={};
let severityList=[], severity="";

// ===== SESSION =====
if(localStorage.room){
  room = localStorage.room;
  name = localStorage.name;
  myId = localStorage.myId;
  isDM = localStorage.isDM==="true";
  start();
}

// ===== LOAD JSON =====
fetch("crit_fails.json").then(r=>r.json()).then(j=>{
  data=j;
  buildSeverity();
  buildSkills();
});

// ===== DYNAMIC SEVERITY =====
function buildSeverity(){

  const set = new Set();

  if(data["Útok"]){
    Object.values(data["Útok"]).forEach(type=>{
      Object.keys(type).forEach(sev=> set.add(sev));
    });
  }

  if(data["Obrana"]){
    Object.keys(data["Obrana"]).forEach(sev=> set.add(sev));
  }

  if(data["Skill"]){
    Object.values(data["Skill"]).forEach(attr=>{
      Object.values(attr).forEach(skill=>{
        Object.keys(skill).forEach(sev=> set.add(sev));
      });
    });
  }

  severityList = Array.from(set);
  severity = severityList[0];

  renderSeverityButtons();
}

function renderSeverityButtons(){

  const container = document.getElementById("severityButtons");

  let html = "";

  severityList.forEach(sev=>{
    html += `<button id="sev-${sev}" onclick="setSeverity('${sev}')">${sev}</button>`;
  });

  container.innerHTML = html;

  setSeverity(severity);
}

function setSeverity(level){
  severity = level;

  document.querySelectorAll("#severityButtons button").forEach(b=>{
    b.classList.remove("active");
  });

  document.getElementById("sev-"+level)?.classList.add("active");
}
window.setSeverity = setSeverity;

// ===== FALLBACK SYSTEM =====
function getPoolSafe(source){

  if(!source) return [];

  if(source[severity] && source[severity].length > 0){
    return source[severity];
  }

  for(const key in source){
    if(source[key] && source[key].length > 0){
      return source[key];
    }
  }

  return [];
}

// ===== LOBBY =====
function quickJoin(r){
  document.getElementById("room").value = r;
}
window.quickJoin = quickJoin;

onValue(ref(db,"rooms"), snap=>{
  const rooms = snap.val() || {};
  let html="";
  Object.keys(rooms).forEach(r=>{
    html += `<div class="room">${r} <button onclick="quickJoin('${r}')">Join</button></div>`;
  });
  document.getElementById("roomsList").innerHTML = html;
});

// ===== LOGIN =====
async function joinDM(){

  room = val("room");
  name = val("name");
  isDM = true;

  const snap = await get(ref(db,"rooms/"+room+"/players"));
  const p = snap.val();

  if(p && Object.values(p).some(x=>x.name.includes("👑"))){
    alert("DM už existuje");
    return;
  }

  myId = "DM_"+Date.now();

  await set(ref(db,"rooms/"+room+"/players/"+myId),{ name:name+" 👑" });

  save();
  start();
}
window.joinDM = joinDM;

async function joinPlayer(){

  room = val("room");
  name = val("name");

  const snap = await get(ref(db,"rooms/"+room));

  if(!snap.exists()){
    alert("Room neexistuje");
    return;
  }

  const playersSnap = await get(ref(db,"rooms/"+room+"/players"));
  const p = playersSnap.val() || {};

  const existing = Object.entries(p).find(([id,x])=>x.name===name);

  if(existing){
    myId = existing[0];
  } else {
    myId = "P_"+Date.now();
    await set(ref(db,"rooms/"+room+"/players/"+myId),{ name });
  }

  save();
  start();
}
window.joinPlayer = joinPlayer;

// ===== START =====
function start(){

  document.getElementById("setup").style.display="none";
  document.getElementById("app").style.display="block";

  if(isDM){
    document.getElementById("dmPanel").style.display="block";
    document.getElementById("topButtons").innerHTML =
      `<button onclick="deleteRoom()">🗑️</button><button onclick="logout()">Logout</button>`;
  } else {
    document.getElementById("playerPanel").style.display="block";
    document.getElementById("roomName").innerText="Room: "+room;
    document.getElementById("topButtons").innerHTML =
      `<button onclick="logout()">Logout</button>`;
  }

  onDisconnect(ref(db,"rooms/"+room+"/players/"+myId)).remove();

  listenPlayers();
  listenRoom();
  listenMessages();
}

// ===== PLAYERS =====
function listenPlayers(){
  onValue(ref(db,"rooms/"+room+"/players"), snap=>{
    players = snap.val() || {};
    document.getElementById("playersTop").innerText =
      Object.values(players).map(p=>p.name).join(" | ");
  });
}

// ===== ROOM DELETE =====
function listenRoom(){
  onValue(ref(db,"rooms/"+room), snap=>{
    if(!snap.exists()){
      logout();
    }
  });
}

// ===== GENERATE =====
function generateSkill(attr, skill, btn){
  const pool = getPoolSafe(data.Skill?.[attr]?.[skill]);
  render(btn, pool, `Skill (${skill})`);
}
window.generateSkill = generateSkill;

function generateAttack(type, btn){
  const pool = getPoolSafe(data["Útok"]?.[type]);
  render(btn, pool, `Útok (${type})`);
}
window.generateAttack = generateAttack;

function generateDefense(btn){
  const pool = getPoolSafe(data["Obrana"]);
  render(btn, pool, "Obrana");
}
window.generateDefense = generateDefense;

// ===== RENDER =====
function render(btn, pool, label){

  document.querySelectorAll(".card").forEach(e=>e.remove());

  if(!pool || pool.length === 0){
    alert("Žádná data vůbec");
    return;
  }

  const r = pool[Math.floor(Math.random()*pool.length)];

  let playersHTML="";

  Object.entries(players).forEach(([id,p])=>{
    if(!p.name.includes("👑")){
      playersHTML += `<button onclick="send('${id}','${r.effect}')">${p.name}</button>`;
    }
  });

  const div=document.createElement("div");
  div.className="card";

  div.innerHTML=`
    <div class="meta">${severity} | ${label}</div>
    <b>${r.effect}</b><br>
    ${r.roleplay.join("<br>")}<br><br>
    ${playersHTML}
  `;

  btn.after(div);
}

// ===== SEND =====
function send(pid,text){
  set(ref(db,"rooms/"+room+"/msg/"+pid), text);
}
window.send = send;

// ===== RECEIVE =====
function listenMessages(){
  onValue(ref(db,"rooms/"+room+"/msg/"+myId), snap=>{
    if(snap.val()){
      document.getElementById("playerResult").innerText = snap.val();
    }
  });
}

// ===== DELETE =====
function deleteRoom(){
  remove(ref(db,"rooms/"+room));
}
window.deleteRoom = deleteRoom;

// ===== LOGOUT =====
function logout(){
  localStorage.clear();
  location.reload();
}
window.logout = logout;

// ===== HELPERS =====
function val(id){ return document.getElementById(id).value; }

function save(){
  localStorage.room=room;
  localStorage.name=name;
  localStorage.myId=myId;
  localStorage.isDM=isDM;
}

// ===== SKILLS =====
function buildSkills(){

  let html="";

  Object.entries(data.Skill).forEach(([attr,skills])=>{
    html+=`<h4>${attr}</h4>`;
    Object.keys(skills).forEach(s=>{
      html+=`<button onclick="generateSkill('${attr}','${s}', this)">${s}</button>`;
    });
  });

  document.getElementById("skills").innerHTML=html;
}

</script>

</body>
</html>
