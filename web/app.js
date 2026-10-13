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

function markdown(text) {
  if (window.marked && window.DOMPurify) return DOMPurify.sanitize(marked.parse(text || ""));
  const div = document.createElement("div");
  div.textContent = text || "";
  return `<pre>${div.innerHTML}</pre>`;
}

function render(data) {
  // /api/analyse renvoie { rapports: {web?, api?}, analyse_ia } ; les tests simples renvoient directement le rapport.
  const reports = data.rapports ? Object.values(data.rapports) : [data];
  const cases = reports.flatMap((r) => r.cas || []);
  const s = { total: 0, pass: 0, fail: 0 };
  for (const c of cases) { s.total++; c.statut === "PASS" ? s.pass++ : s.fail++; }
  s.taux_reussite = s.total ? Math.round((1000 * s.pass) / s.total) / 10 : 0;
  data = { cas: cases, resume: s, _raw: data };
  const ia = document.getElementById("ia-block");
  ia.hidden = !data._raw.analyse_ia;
  document.getElementById("ia-text").innerHTML = markdown(data._raw.analyse_ia);
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
  document.getElementById("summary").textContent =
    `${s.total} cas — ${s.pass} PASS / ${s.fail} FAIL (${s.taux_reussite} %)`;
  document.getElementById("raw").textContent = JSON.stringify(data._raw, null, 2);
  card.hidden = false;
  card.scrollIntoView({ behavior: "smooth" });
}

async function run(path, payload, button) {
  button.disabled = true;
  const label = button.textContent;
  button.textContent = path === "/api/analyse" ? "Tests + analyse IA (≈30 s)…" : "Test en cours…";
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

// Bouton « Tester + analyse IA » -> /api/analyse ; sinon test simple.
function submit(kind, payload, button) {
  if (button.value === "analyse") return run("/api/analyse", { [kind]: payload }, button);
  return run(`/api/test/${kind}`, payload, button);
}

document.getElementById("web-form").addEventListener("submit", (e) => {
  e.preventDefault();
  submit("web", {
    url: document.getElementById("web-url").value,
    max_links: Number(document.getElementById("web-links").value),
  }, e.submitter);
});

// --- Chat avec l'agent Abacus.AI via le backend Railway ---
const history = [];
const chatLog = document.getElementById("chat-log");

// --- Pipeline : code fourni par l'agent -> Pull Request GitHub ---
const devMode = document.getElementById("dev-mode");
const autoPr = document.getElementById("auto-pr");
const keyInput = document.getElementById("pipeline-key");
for (const [el, key] of [[devMode, "devMode"], [autoPr, "autoPr"]]) {
  el.checked = localStorage.getItem(key) === "1";
  el.addEventListener("change", () => localStorage.setItem(key, el.checked ? "1" : "0"));
}
keyInput.value = localStorage.getItem("pipelineKey") || "";
keyInput.addEventListener("change", () => localStorage.setItem("pipelineKey", keyInput.value.trim()));

async function pipeline(payload) {
  const res = await fetch(`${backend}/api/pipeline/pr`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Pipeline-Secret": keyInput.value.trim() },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Erreur HTTP ${res.status}`);
  return data;
}

// Après chaque réponse : détecte les fichiers ; propose (ou crée automatiquement) la PR.
async function detectCode(reply, question, bubble) {
  if (!devMode.checked || !reply.includes("```")) return;
  let found;
  try { found = await pipeline({ texte: reply, dry_run: true }); }
  catch { return; } // aucun fichier avec chemin : réponse sans code à livrer
  const box = document.createElement("div");
  box.className = "pr-box";
  const list = found.fichiers.map((f) => `<code>${f.replace(/</g, "&lt;")}</code>`).join(", ");
  box.innerHTML = `<div>📦 ${found.fichiers.length} fichier(s) détecté(s) : ${list}</div>`;
  const btn = document.createElement("button");
  btn.className = "btn btn-ia";
  btn.textContent = "Créer la Pull Request";
  const status = document.createElement("div");
  box.append(btn, status);
  bubble.after(box);
  const create = async () => {
    btn.disabled = true;
    status.textContent = "Création de la PR…";
    try {
      const pr = await pipeline({ texte: reply, titre: `Abacus : ${question.slice(0, 80)}`,
                                  description: `Demande : ${question}` });
      btn.remove();
      status.innerHTML = `✅ <a href="${pr.url}" target="_blank" rel="noopener">PR n°${pr.numero}</a>
        créée (branche <code>${pr.branche}</code>). La CI et la prévisualisation Vercel démarrent.`;
    } catch (err) {
      btn.disabled = false;
      status.textContent = `Échec : ${err.message}`;
    }
  };
  btn.addEventListener("click", create);
  if (autoPr.checked) create();
}

function addBubble(text, isUser) {
  const div = document.createElement("div");
  div.className = `bubble ${isUser ? "user" : "agent"}`;
  if (isUser) div.textContent = text; else div.innerHTML = markdown(text);
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  history.push({ is_user: true, text });
  addBubble(text, true);
  const pending = addBubble("_L'agent réfléchit…_", false);
  const button = e.submitter;
  button.disabled = true;
  try {
    const res = await fetch(`${backend}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history, mode_dev: devMode.checked }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `Erreur HTTP ${res.status}`);
    history.push({ is_user: false, text: data.reponse });
    pending.innerHTML = markdown(data.reponse);
    detectCode(data.reponse, text, pending);
  } catch (err) {
    history.pop();
    pending.textContent = `Échec : ${err.message}`;
    pending.classList.add("error");
  } finally {
    button.disabled = false;
  }
});

document.getElementById("api-form").addEventListener("submit", (e) => {
  e.preventDefault();
  try {
    const keys = document.getElementById("api-keys").value
      .split(",").map((k) => k.trim()).filter(Boolean);
    submit("api", {
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
