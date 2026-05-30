const state = {
  selectedFiles: []
};

document.addEventListener("DOMContentLoaded", () => {
  bindControls();
  refreshStatus();
  analyze();
  loadModelDetails();
});

function bindControls() {
  const input = document.getElementById("fileInput");
  const dropzone = document.getElementById("dropzone");
  input.addEventListener("change", () => {
    state.selectedFiles = [...input.files];
  });
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("is-dragging");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-dragging"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragging");
    state.selectedFiles = [...event.dataTransfer.files];
    input.files = event.dataTransfer.files;
  });
  document.getElementById("uploadButton").addEventListener("click", uploadFiles);
  document.getElementById("analyzeButton").addEventListener("click", analyze);
  document.getElementById("runButton").addEventListener("click", runAudit);
  document.getElementById("saveProfileButton").addEventListener("click", saveProfile);
}

async function refreshStatus() {
  const payload = await fetchJson("/api/status");
  document.getElementById("workspaceLabel").textContent = payload.workspace;
}

async function saveProfile() {
  const systems = [...document.querySelectorAll("#systemGrid input:checked")].map((input) => input.value);
  const payload = {
    systems,
    staffing_owner: document.getElementById("ownerInput").value,
    notes: document.getElementById("notesInput").value,
    saved_at: new Date().toISOString()
  };
  await fetch("/api/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  setOutput("Profile saved locally. Drop copied exports next.");
}

async function uploadFiles() {
  if (!state.selectedFiles.length) {
    setOutput("Select or drop files first.");
    return;
  }
  const form = new FormData();
  state.selectedFiles.forEach((file) => form.append("files", file));
  const response = await fetch("/api/upload", { method: "POST", body: form });
  const payload = await response.json();
  renderSummary(payload.summary);
  setOutput(`Uploaded ${payload.saved.length} file(s). Intake summary refreshed.`);
}

async function analyze() {
  const payload = await fetchJson("/api/analyze");
  renderSummary(payload);
}

async function runAudit() {
  setOutput("Running local AMDEP audit. Keep this browser open.");
  const response = await fetch("/api/run-audit", { method: "POST" });
  const payload = await response.json();
  if (!payload.ok) {
    renderSummary(payload.summary);
    setOutput(`<strong>Audit could not run yet.</strong><br>${escapeHtml(payload.error)}`);
    return;
  }
  setOutput(`
    <strong>Audit complete.</strong><br>
    18-month impact: ${money(payload.impact_18_month)}<br>
    Annual run-rate: ${money(payload.annual_run_rate)}<br>
    <a href="${payload.report_url}" target="_blank" rel="noreferrer">Open executive audit packet</a><br>
    ${payload.command_url ? `<a href="${payload.command_url}" target="_blank" rel="noreferrer">Open local command center</a><br>` : ""}
    <small>${escapeHtml(payload.output_dir)}</small>
  `);
  loadModelDetails();
}

function renderSummary(summary) {
  document.getElementById("workspaceLabel").textContent = summary.workspace;
  document.getElementById("scoreValue").textContent = `${summary.readiness.score}%`;
  document.getElementById("scoreStatus").textContent = summary.readiness.status.replaceAll("_", " ");
  document.getElementById("scoreNotes").innerHTML = (summary.readiness.notes || [])
    .map((note) => `<li>${escapeHtml(note)}</li>`)
    .join("") || "<li>No immediate blockers found.</li>";
  const files = summary.files || [];
  document.getElementById("fileList").innerHTML = files.length
    ? files.map(fileCard).join("")
    : `<div class="output-box">No files found. Drop copied exports or place files in the workspace inbox.</div>`;
}

function fileCard(file) {
  const confidence = Math.round(Number(file.confidence || 0) * 100);
  const warn = confidence < 50 || file.classification === "unknown";
  return `
    <article class="file-card">
      <div>
        <strong>${escapeHtml(file.file)}</strong>
        <small>${escapeHtml(file.label)} | ${confidence}% confidence | ${file.columns.length} detected columns</small>
        <small>Mapped: ${Object.keys(file.mapped_columns || {}).join(", ") || "none"}</small>
      </div>
      <span class="pill ${warn ? "warn" : ""}">${escapeHtml(file.classification)}</span>
    </article>
  `;
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

async function loadModelDetails() {
  const payload = await fetchJson("/api/model");
  document.getElementById("modelFamilies").innerHTML = payload.model_families
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  document.getElementById("defaultWeights").innerHTML = Object.entries(payload.default_weights)
    .map(([key, value]) => `<div><span>${escapeHtml(key.replaceAll("_", " "))}</span><strong>${Number(value).toFixed(2)}</strong></div>`)
    .join("");
  const latest = payload.latest_run || {};
  const latestWeights = latest.recommended_weights || [];
  if (!latestWeights.length) {
    document.getElementById("latestWeights").textContent = "Run an audit to generate recommended weights.";
    return;
  }
  document.getElementById("latestWeights").innerHTML = `
    <div class="weight-list">
      ${latestWeights.map((row) => `<div><span>${escapeHtml(row.weight)}</span><strong>${Number(row.value).toFixed(3)}</strong></div>`).join("")}
    </div>
    ${latest.recommended_weights_url ? `<a href="${latest.recommended_weights_url}" target="_blank" rel="noreferrer">Open recommended_weights.csv</a>` : ""}
  `;
}

function setOutput(html) {
  document.getElementById("outputBox").innerHTML = html;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(Number(value || 0));
}
