#!/usr/bin/env node
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const HOME = process.env.HOME || process.cwd();
const AIFT_HOME = process.env.AIFT_HOME || path.resolve(__dirname, "../..");
const AIFT_TRUSTS = process.env.AIFT_TRUSTS || path.join(HOME, "AIFT-Trusts");
const PORT = Number(process.env.PORT || process.env.AIFT_PORT || 8787);
const HOST = process.env.HOST || "127.0.0.1";

const REQUIRED_FILES = [
  "README.md",
  "TRUST.md",
  "IDENTITY.md",
  "VALUES.md",
  "GOVERNANCE.md",
  "AI_STEWARD.md",
  "TREE_OF_LIFE.md",
  "MAP.md",
  "ECONOMY.md",
  "FEDERATION_LINK.md",
  "LOCAL_MANIFEST.json"
];

function json(res, status, data) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data, null, 2));
}

function html(res, body) {
  res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  res.end(body);
}

function safeTrustPath(input) {
  const raw = input || "";
  const candidate = raw.startsWith("/") ? raw : path.join(AIFT_TRUSTS, raw);
  const resolved = path.resolve(candidate);
  const trustsRoot = path.resolve(AIFT_TRUSTS);
  if (!resolved.startsWith(trustsRoot)) {
    throw new Error("Trust path must be inside AIFT_TRUSTS");
  }
  return resolved;
}

function readText(file) {
  return fs.readFileSync(file, "utf8");
}

function parseJsonFile(file) {
  return JSON.parse(readText(file));
}

function listTrusts() {
  if (!fs.existsSync(AIFT_TRUSTS)) return [];
  return fs.readdirSync(AIFT_TRUSTS, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => {
      const trustPath = path.join(AIFT_TRUSTS, d.name);
      let manifest = null;
      try {
        manifest = parseJsonFile(path.join(trustPath, "LOCAL_MANIFEST.json"));
      } catch {}
      return {
        slug: d.name,
        path: trustPath,
        name: manifest?.trust?.name || d.name,
        purpose: manifest?.trust?.purpose || "",
        status: manifest?.trust?.maturity || "unknown",
        federation: manifest?.federationLink?.status || "unknown"
      };
    });
}

function validateTrust(trustPath) {
  const errors = [];
  const warnings = [];
  for (const file of REQUIRED_FILES) {
    if (!fs.existsSync(path.join(trustPath, file))) errors.push(`missing required file: ${file}`);
  }

  for (const file of fs.readdirSync(trustPath)) {
    const full = path.join(trustPath, file);
    if (!fs.statSync(full).isFile()) continue;
    if (!file.endsWith(".md") && !file.endsWith(".json")) continue;
    const text = readText(full);
    if (/{{TRUST_NAME}}|{{TRUST_SLUG}}|{{TRUST_PURPOSE}}/.test(text)) {
      errors.push(`unreplaced generator variable in ${file}`);
    }
    if (/\bTODO\b|\bFIXME\b|\bXXX\b|<\s*(fill\s*in|insert|todo|replace)[^>]*>|\[\s*(insert|fill\s*in|todo|replace)[^\]]*\]/i.test(text)) {
      errors.push(`unfinished marker in ${file}`);
    }
    if (file.endsWith(".json")) {
      try { JSON.parse(text); } catch (err) { errors.push(`invalid JSON in ${file}: ${err.message}`); }
    }
  }

  try {
    const status = execFileSync("git", ["-C", trustPath, "status", "--porcelain"], { encoding: "utf8" });
    if (status.trim()) warnings.push("git working tree has uncommitted files");
  } catch {
    errors.push("trust is not a git repository");
  }

  return { ok: errors.length === 0, errors, warnings };
}

function trustSummary(trustPath) {
  const manifestPath = path.join(trustPath, "LOCAL_MANIFEST.json");
  const manifest = fs.existsSync(manifestPath) ? parseJsonFile(manifestPath) : null;
  return {
    path: trustPath,
    manifest,
    validation: validateTrust(trustPath),
    files: REQUIRED_FILES.filter((file) => fs.existsSync(path.join(trustPath, file)))
  };
}

function page() {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AIFT Genesis</title>
  <style>
    :root { color-scheme: dark; font-family: system-ui, sans-serif; }
    body { margin: 0; background: #07100d; color: #eef7ef; }
    header { padding: 28px 20px; background: radial-gradient(circle at top, #214d3d, #07100d 70%); border-bottom: 1px solid #25483d; }
    main { max-width: 1100px; margin: 0 auto; padding: 20px; }
    h1 { margin: 0; font-size: 2rem; }
    .sub { color: #b7c9bf; margin-top: 8px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin-top: 20px; }
    .card { background: #0d1b17; border: 1px solid #25483d; border-radius: 14px; padding: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.25); }
    button { background: #59d58b; color: #06100b; border: 0; padding: 10px 12px; border-radius: 10px; font-weight: 700; cursor: pointer; }
    button.secondary { background: #19352c; color: #e7f7ed; border: 1px solid #376653; }
    input, textarea { width: 100%; box-sizing: border-box; margin: 6px 0 12px; padding: 10px; border-radius: 10px; border: 1px solid #376653; background: #07100d; color: #eef7ef; }
    pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #06100b; border: 1px solid #1f3b32; border-radius: 12px; padding: 12px; }
    .ok { color: #75f0a1; }
    .warn { color: #ffd166; }
    .err { color: #ff7b7b; }
    a { color: #75f0a1; }
  </style>
</head>
<body>
  <header>
    <main>
      <h1>AIFT Genesis Dashboard</h1>
      <div class="sub">Local-first trust runtime. Private by default. Federation by consent.</div>
    </main>
  </header>
  <main>
    <section class="grid">
      <div class="card">
        <h2>Create Trust</h2>
        <label>Trust name</label>
        <input id="trustName" placeholder="Example: Zechariah Family Trust" />
        <label>Trust purpose</label>
        <textarea id="trustPurpose" rows="5" placeholder="Describe what this trust stewards..."></textarea>
        <button onclick="createTrust()">Create Trust</button>
      </div>
      <div class="card">
        <h2>Trusts</h2>
        <button class="secondary" onclick="loadTrusts()">Refresh Trusts</button>
        <div id="trusts"></div>
      </div>
      <div class="card">
        <h2>Runtime Actions</h2>
        <button class="secondary" onclick="loadTrusts().then(()=>validateSelected())">Validate Selected</button>
        <button class="secondary" onclick="showSteward()">AI Steward Context</button>
        <button class="secondary" onclick="showAtlas()">Living Atlas Context</button>
        <p class="sub">These buttons are the first UX layer over the same runtime contracts proven in Termux.</p>
      </div>
    </section>
    <section class="card" style="margin-top:16px">
      <h2>Output</h2>
      <pre id="output">Loading...</pre>
    </section>
  </main>
<script>
let selected = null;
function out(value) { document.getElementById('output').textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); }
async function api(path, options) { const r = await fetch(path, options); const j = await r.json(); if (!r.ok) throw j; return j; }
async function loadTrusts() {
  const data = await api('/api/trusts');
  const box = document.getElementById('trusts');
  box.innerHTML = data.trusts.map(t => `<div style="margin:10px 0"><button class="secondary" onclick="selectTrust('${t.slug}')">${t.name}</button><div class="sub">${t.slug}</div></div>`).join('') || '<p class="sub">No trusts found yet.</p>';
  if (!selected && data.trusts[0]) selected = data.trusts[0].slug;
  out(data);
  return data;
}
async function selectTrust(slug) { selected = slug; const data = await api('/api/trust/' + encodeURIComponent(slug)); out(data); }
async function validateSelected() { if (!selected) return out('No trust selected.'); const data = await api('/api/validate/' + encodeURIComponent(selected)); out(data); }
async function createTrust() {
  const name = document.getElementById('trustName').value.trim();
  const purpose = document.getElementById('trustPurpose').value.trim();
  if (!name) return out('Trust name is required.');
  const data = await api('/api/create', { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify({ name, purpose }) });
  selected = data.slug;
  await loadTrusts();
  out(data);
}
function showSteward() { out('AI Steward must read: TRUST.md, IDENTITY.md, VALUES.md, GOVERNANCE.md, AI_STEWARD.md, LOCAL_MANIFEST.json before acting.'); }
function showAtlas() { out('Living Atlas source documents: MAP.md, TREE_OF_LIFE.md, LOCAL_MANIFEST.json. Green Zone remains private by default.'); }
loadTrusts().catch(out);
</script>
</body>
</html>`;
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

function runAift(args, input = "") {
  return execFileSync(path.join(AIFT_HOME, "bin", "aift"), args, {
    cwd: AIFT_HOME,
    input,
    encoding: "utf8",
    env: { ...process.env, AIFT_HOME, AIFT_TRUSTS }
  });
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === "/") return html(res, page());
    if (url.pathname === "/api/trusts") return json(res, 200, { trusts: listTrusts() });
    if (url.pathname.startsWith("/api/trust/")) {
      const slug = decodeURIComponent(url.pathname.replace("/api/trust/", ""));
      return json(res, 200, trustSummary(safeTrustPath(slug)));
    }
    if (url.pathname.startsWith("/api/validate/")) {
      const slug = decodeURIComponent(url.pathname.replace("/api/validate/", ""));
      const trustPath = safeTrustPath(slug);
      return json(res, 200, { path: trustPath, validation: validateTrust(trustPath) });
    }
    if (url.pathname === "/api/create" && req.method === "POST") {
      const body = JSON.parse(await readBody(req) || "{}");
      if (!body.name) return json(res, 400, { error: "Trust name is required" });
      const purpose = body.purpose || "A local-first trust generated from the AIFT Genesis constitutional genome.";
      runAift(["trust", "init", body.name], `${purpose}\n`);
      const slug = body.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      return json(res, 200, { ok: true, slug, path: path.join(AIFT_TRUSTS, slug) });
    }
    json(res, 404, { error: "Not found" });
  } catch (err) {
    json(res, 500, { error: err.message || String(err) });
  }
});

server.listen(PORT, HOST, () => {
  console.log(`AIFT Genesis Dashboard running at http://${HOST}:${PORT}`);
  console.log(`AIFT_HOME=${AIFT_HOME}`);
  console.log(`AIFT_TRUSTS=${AIFT_TRUSTS}`);
});
