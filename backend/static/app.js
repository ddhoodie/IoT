async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(body || {})
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = json?.error || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return json;
}

function fmtBool(v) { return v ? "ON" : "OFF"; }
function fmtTs(ts) {
  try { return new Date(ts * 1000).toLocaleString(); } catch { return "-"; }
}
function fmtRgb(rgb) {
  if (!rgb) return "-";
  return `${rgb.on ? "ON" : "OFF"} (${rgb.r},${rgb.g},${rgb.b})`;
}
function fmtTimer(t) {
  if (!t) return "-";
  const left = t.seconds_left ?? 0;
  const s = `${left}s` + (t.running ? " (running)" : "") + (t.finished ? " (finished)" : "");
  return s;
}

let lastAlarm = false;

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2500);
}

function hexToRgb(hex) {
  const h = (hex || "#000000").replace("#", "");
  const r = parseInt(h.substring(0,2), 16);
  const g = parseInt(h.substring(2,4), 16);
  const b = parseInt(h.substring(4,6), 16);
  return {r,g,b};
}

function renderDevices(devices) {
  const container = document.getElementById("devicesList");
  if (!container) return;

  const codes = Object.keys(devices || {}).sort();
  if (codes.length === 0) {
    container.innerHTML = '<p class="muted">Waiting for data...</p>';
    return;
  }

  let html = "";
  for (const code of codes) {
    const d = devices[code];
    let valStr = JSON.stringify(d.value);
    if (typeof d.value === "object" && d.value !== null) {
      valStr = Object.entries(d.value).map(([k,v]) => `${k}:${v}`).join(", ");
    }

    html += `
      <div class="device-item">
        <div class="device-header">
          <span class="device-name">${d.device || code} (${code})</span>
          <span class="muted">${new Date(d.timestamp * 1000).toLocaleTimeString()}</span>
        </div>
        <div class="device-val">${valStr}</div>
      </div>
    `;
  }
  container.innerHTML = html;
}

function render(state) {
  document.getElementById("armed").textContent = fmtBool(state.armed);
  document.getElementById("alarm").textContent = fmtBool(state.alarm);
  document.getElementById("reason").textContent = state.last_alarm_reason || "-";
  document.getElementById("people").textContent = String(state.people_count ?? 0);
  document.getElementById("timer").textContent = fmtTimer(state.timer);
  document.getElementById("rgb").textContent = fmtRgb(state.rgb);
  document.getElementById("ts").textContent = fmtTs(state.last_update_ts);

  document.getElementById("nsecLabel").textContent = String(state.timer?.add_n_seconds ?? "-");

  renderDevices(state.devices);

  // alarm toast
  if (!lastAlarm && state.alarm) {
    toast(`ALARM ON (${state.last_alarm_reason || "unknown"})`);
  }
  lastAlarm = !!state.alarm;
}

async function refresh() {
  try {
    const state = await apiGet("/api/state");
    render(state);
  } catch (e) {
    console.error(e);
  }
}

function wire() {
  const pinEl = document.getElementById("pin");

  document.getElementById("btnArm").onclick = async () => {
    try { await apiPost("/api/alarm/arm", {pin: pinEl.value}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnDisarm").onclick = async () => {
    try { await apiPost("/api/alarm/disarm", {pin: pinEl.value}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnStopAlarm").onclick = async () => {
    try { await apiPost("/api/alarm/stop", {pin: pinEl.value}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnTriggerDoor").onclick = async () => {
    try { await apiPost("/api/alarm/trigger", {reason:"door_unlock>5s"}); await refresh(); }
    catch(e){ toast(e.message); }
  };
  document.getElementById("btnTriggerMotion").onclick = async () => {
    try { await apiPost("/api/alarm/trigger", {reason:"motion_when_empty"}); await refresh(); }
    catch(e){ toast(e.message); }
  };
  document.getElementById("btnTriggerGsg").onclick = async () => {
    try { await apiPost("/api/alarm/trigger", {reason:"gsg_moved"}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnIn").onclick = async () => {
    try { await apiPost("/api/people", {delta: 1}); await refresh(); }
    catch(e){ toast(e.message); }
  };
  document.getElementById("btnOut").onclick = async () => {
    try { await apiPost("/api/people", {delta: -1}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnSetTimer").onclick = async () => {
    const seconds = parseInt(document.getElementById("timerSeconds").value || "0", 10);
    try { await apiPost("/api/timer/set", {seconds}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnAddTimer").onclick = async () => {
    try { await apiPost("/api/timer/add", {}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnSetN").onclick = async () => {
    const n_seconds = parseInt(document.getElementById("nsec").value || "1", 10);
    try { await apiPost("/api/timer/add_config", {n_seconds}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  document.getElementById("btnRgbApply").onclick = async () => {
    const on = document.getElementById("rgbOn").checked;
    const hex = document.getElementById("rgbColor").value;
    const {r,g,b} = hexToRgb(hex);
    try { await apiPost("/api/rgb", {on,r,g,b}); await refresh(); }
    catch(e){ toast(e.message); }
  };

  const sensorSelect = document.getElementById("sensorSelect");
  const grafanaFrame = document.getElementById("grafanaFrame");
  if (sensorSelect && grafanaFrame) {
    sensorSelect.onchange = () => {
      const panelId = sensorSelect.value;
      const baseUrl = "http://localhost:3000/d-solo/iot-dashboard/iot-system-dashboard";
      const params = `?orgId=1&panelId=${panelId}&refresh=5s&theme=dark`;
      grafanaFrame.src = baseUrl + params;
    };
  }
}

wire();
refresh();
setInterval(refresh, 1000);

