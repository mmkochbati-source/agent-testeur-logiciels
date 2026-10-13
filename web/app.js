const { BACKEND_URL, AGENT_URL } = window.APP_CONFIG;
const backend = BACKEND_URL.replace(/\/$/, "");
document.getElementById("agent-link").href = AGENT_URL;
document.getElementById("backend-url").textContent = backend;

function parseJsonField(id, label) {
  const raw = document.getElementById(id).value.trim();
  if (!raw) return undefined;
  try { return JSON.parse(raw); }
  catch { throw new Error(`${label} : JSON invalide`); }
}

function render(data) {
  const card = document.getElementById("result-card");
  const tbody = document.getElementById("results");
  tbody.innerHTML = "";
  for (const c of data.cas || []) {
    const tr = document.createElement("tr");
    for (const v of [c.id, c.description, c.attendu, c.obtenu, c.statut]) {
      const td = document.createElement("td");
      td.textContent = v;
      tr.appendChild(td);
    }
    tr.lastChild.className = c.statut === "PASS" ? "pass" : "fail";
    tbody.appendChild(tr);
  }
  const s = data.resume || {};
  document.getElementById("summary").textContent =
    `${s.total ?? 0} cas — ${s.pass ?? 0} PASS / ${s.fail ?? 0} FAIL (${s.taux_reussite ?? 0} %)`;
  document.getElementById("raw").textContent = JSON.stringify(data, null, 2);
  card.hidden = false;
  card.scrollIntoView({ behavior: "smooth" });
}

async function run(path, payload, button) {
  button.disabled = true;
  const label = button.textContent;
  button.textContent = "Test en cours…";
  try {
    const res = await fetch(`${backend}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `Erreur HTTP ${res.status}`);
    render(data);
  } catch (e) {
    alert(`Échec : ${e.message}`);
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

document.getElementById("web-form").addEventListener("submit", (e) => {
  e.preventDefault();
  run("/api/test/web", {
    url: document.getElementById("web-url").value,
    max_links: Number(document.getElementById("web-links").value),
  }, e.submitter);
});

document.getElementById("api-form").addEventListener("submit", (e) => {
  e.preventDefault();
  try {
    const keys = document.getElementById("api-keys").value
      .split(",").map((k) => k.trim()).filter(Boolean);
    run("/api/test/api", {
      method: document.getElementById("api-method").value,
      url: document.getElementById("api-url").value,
      expected_status: Number(document.getElementById("api-status").value),
      expected_keys: keys,
      headers: parseJsonField("api-headers", "En-têtes") || {},
      body: parseJsonField("api-body", "Corps"),
    }, e.submitter);
  } catch (err) {
    alert(err.message);
  }
});
