const DATA_BASE = "../reports/demo_audit/";
const EXPORT_BASE = `${DATA_BASE}integrations/`;
const DECISION_KEY = "amdep.demo.decisions.v1";

const FILES = {
  baseline: `${DATA_BASE}baseline_assignments.csv`,
  optimized: `${DATA_BASE}optimized_assignments.csv`,
  waste: `${DATA_BASE}top_waste_findings.csv`,
  burden: `${DATA_BASE}personnel_burden.csv`,
  staffing: `${DATA_BASE}job_staffing_status.csv`,
  robotics: `${DATA_BASE}robotics_plan.csv`,
  trials: `${DATA_BASE}calibration_trials.csv`,
  weights: `${DATA_BASE}recommended_weights.csv`,
  recommendations: `${EXPORT_BASE}recommendations_generic.csv`
};

const EXPORTS = [
  ["Generic review CSV", "recommendations_generic.csv", "Excel, BI, or ops review"],
  ["Procore Resource Planning", "procore_resource_planning_recommendations.csv", "project and person queue"],
  ["Autodesk Construction Cloud", "autodesk_construction_cloud_recommendations.csv", "project workflow handoff"],
  ["HCSS HeavyJob", "hcss_heavyjob_crew_equipment_recommendations.csv", "field leadership and equipment"],
  ["Sage Construction", "sage_construction_recommendations.csv", "project labor draft"],
  ["Warranty / service queue", "servicetitan_appointment_recommendations.csv", "service or warranty group review"],
  ["Specialty ops extract", "acculynx_roofing_recommendations.csv", "specialty production review"],
  ["Foundry objects", "foundry_object_imports.json", "ontology-style import payload"]
];

const REGION_POINTS = {
  "Sarasota-Punta Gorda": [300, 58],
  "Cape Coral": [229, 143],
  "Fort Myers": [262, 154],
  "Lehigh-Immokalee": [322, 188],
  "Bonita-Estero": [250, 222],
  "Naples": [230, 275]
};

const FALLBACK_POINTS = [
  [204, 106],
  [286, 116],
  [208, 184],
  [306, 238],
  [246, 305]
];

const REGION_COORDS = {
  "Naples": [26.1420, -81.7948],
  "Bonita-Estero": [26.3398, -81.7787],
  "Fort Myers": [26.6406, -81.8723],
  "Cape Coral": [26.5629, -81.9495],
  "Lehigh-Immokalee": [26.6253, -81.5767],
  "Sarasota-Punta Gorda": [27.1270, -82.0200]
};

let dispatchMap = null;

const state = {
  data: {},
  economics: {},
  decisions: loadDecisions(),
  filter: "all",
  analysisRun: false
};

document.addEventListener("DOMContentLoaded", () => {
  bindNavigation();
  bindControls();
  registerServiceWorker();
  window.addEventListener("hashchange", restoreSectionFromHash);
  restoreSectionFromHash();
  loadPacket();
});

function bindNavigation() {
  document.querySelectorAll("[data-section-link]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      showSection(link.dataset.sectionLink);
    });
  });
}

function bindControls() {
  document.getElementById("refreshButton")?.addEventListener("click", loadPacket);
  document.getElementById("runAnalysisButton")?.addEventListener("click", runAnalysis);
  document.querySelectorAll(".filter-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      document.querySelectorAll(".filter-button").forEach((item) => item.classList.toggle("is-active", item === button));
      renderRecommendations();
    });
  });
}

function showSection(sectionId) {
  document.querySelectorAll("[data-section]").forEach((section) => {
    section.classList.toggle("is-hidden", section.id !== sectionId);
  });
  document.querySelectorAll("[data-section-link]").forEach((link) => {
    link.classList.toggle("is-active", link.dataset.sectionLink === sectionId);
  });
  history.replaceState(null, "", `#${sectionId}`);
}

function restoreSectionFromHash() {
  const sectionId = location.hash.replace("#", "") || "overview";
  if (document.getElementById(sectionId)) {
    showSection(sectionId);
  }
}

async function loadPacket() {
  state.analysisRun = false;
  document.body.classList.remove("analysis-complete");
  setSync("Loading portfolio");
  try {
    state.data = await fetchJson("./demo-data.json");
    renderAll();
    setSync("Portfolio loaded");
  } catch {
    try {
      const entries = await Promise.all(
        Object.entries(FILES).map(async ([key, path]) => [key, await fetchCsv(path)])
      );
      state.data = Object.fromEntries(entries);
      state.economics = {};
      renderAll();
      setSync("Portfolio loaded");
    } catch (error) {
      console.error(error);
      setSync("Portfolio missing");
      document.getElementById("recommendationList").innerHTML = `<div class="empty-state">Could not load the generated audit packet. Run <strong>python -m amdep.web_demo</strong> from the repository root.</div>`;
    }
  }
}

function runAnalysis() {
  state.analysisRun = true;
  document.body.classList.add("analysis-complete");
  renderAll();
  setSync("Analysis complete");
  setText("runAnalysisButton", "Run again");
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  const payload = await response.json();
  state.economics = payload.economics || {};
  return payload.tables;
}

async function loadLegacyCsvPacket() {
  const entries = await Promise.all(
    Object.entries(FILES).map(async ([key, path]) => [key, await fetchCsv(path)])
  );
  return Object.fromEntries(entries);
}

function renderAll() {
  renderMetrics();
  renderRouteVisual();
  renderWeights();
  renderRecommendations();
  renderMobilePreview();
  renderExports();
}

function renderMetrics() {
  const baselineHours = routeHours(state.data.baseline);
  const optimizedHours = routeHours(state.data.optimized);
  const delta = Math.max(0, baselineHours - optimizedHours);
  const economics = deriveEconomics(delta);
  const staffing = state.data.staffing || [];
  const fullyStaffed = staffing.filter((row) => boolish(row.fully_staffed)).length;
  const staffedPct = staffing.length ? fullyStaffed / staffing.length : 0;
  const coverageGaps = sum(staffing, "unfilled_slots");
  const burdenWatch = (state.data.burden || []).filter((row) => ["Medium", "High"].includes(row.burden_band)).length;
  const roboticsTrips = sum(state.data.robotics || [], "estimated_avoidable_trips");
  const trials = state.data.trials || [];
  const recommendations = state.data.recommendations || [];
  const best = trials.length ? Number(trials[0].policy_cost || 0) : 0;
  const last = trials.length ? Number(trials[trials.length - 1].policy_cost || best) : best;
  const signal = best && last ? Math.max(0, Math.min(99, Math.round((1 - best / Math.max(best, last)) * 100 + 72))) : 86;
  const wasteCount = (state.data.waste || []).length;

  setText("baselineHours", `${baselineHours.toFixed(1)}h`);
  setText("conflictCount", String(wasteCount));
  setText("coverageGaps", String(coverageGaps || 0));
  setText("optimizedHours", state.analysisRun ? `${optimizedHours.toFixed(1)}h` : "--");
  setText("deltaHours", state.analysisRun ? `${delta.toFixed(1)}h` : "--");
  setText("annualSavings", state.analysisRun ? money(economics.implementationImpact) : "--");
  setText("staffedPct", state.analysisRun ? percent(staffedPct) : "--");
  setText("staffedCaption", state.analysisRun ? `${fullyStaffed} of ${staffing.length} projects fully covered` : "Run analysis to compare coverage");
  setText("burdenCount", String(burdenWatch));
  setText("roboticsTrips", state.analysisRun ? String(roboticsTrips || 0) : "--");
  setText("reviewQueueCount", state.analysisRun ? String(recommendations.length) : "--");
  setText("coverageSummary", staffing.length ? `${fullyStaffed}/${staffing.length}` : "--");
  setText("verificationSummary", `${roboticsTrips || 0} trips`);
  setText("grossOpportunity", state.analysisRun ? money(economics.annualRunRate) : "--");
  setText("profitLeverage", state.analysisRun ? percent(economics.profitLeverage) : "--");
  renderLeakGrid(economics);
  setText("wasteCount", `${wasteCount} findings`);
  setText("brainSignal", state.analysisRun ? `${signal}% fit` : "Ready");
  setText("brainCaption", state.analysisRun ? `${trials.length || 0} scenario trials on synthetic data` : "Synthetic GC portfolio loaded");
  setText("runAnalysisButton", state.analysisRun ? "Run review again" : "Run ML staffing review");
}

function renderRouteVisual() {
  const waste = (state.data.waste || []).slice(0, 7);
  const container = document.getElementById("routeVisual");
  resetDispatchMap();
  if (!waste.length) {
    container.innerHTML = `<div class="empty-state">No waste findings in the current packet.</div>`;
    return;
  }
  if (window.L && (state.data.workers || []).length && (state.data.jobsites || []).length) {
    renderLeafletRouteMap(waste, container);
    return;
  }
  const baselineLookup = Object.fromEntries((state.data.baseline || []).map((row) => [row.assignment_id, row]));
  const maxMinutes = Math.max(...waste.map((row) => Number(row.avoidable_minutes_one_way || 0)), 1);
  const conflictLines = waste.map((row, index) => {
    const assignment = baselineLookup[row.assignment_id] || {};
    const from = regionPoint(assignment.home_region || row.home_region || "", index);
    const to = regionPoint(assignment.job_region || row.job_region || row.job_name || "", index + 2);
    const avoidable = Number(row.avoidable_minutes_one_way || 0);
    const intensity = Math.max(0.35, avoidable / maxMinutes);
    const width = 2.5 + intensity * 4.5;
    const stroke = index < 3 ? "#b83224" : "#bd6f1c";
    return `
      <g opacity="${0.58 + intensity * 0.34}">
        <path d="${conflictPath(from, to, index)}" fill="none" stroke="${stroke}" stroke-width="${width.toFixed(1)}" stroke-linecap="round"/>
        <circle cx="${from[0]}" cy="${from[1]}" r="4.2" fill="#343a40"/>
        <circle cx="${to[0]}" cy="${to[1]}" r="5.5" fill="${stroke}"/>
      </g>
    `;
  }).join("");
  const regionNodes = Object.entries(REGION_POINTS).map(([region, [x, y]]) => `
    <g>
      <circle cx="${x}" cy="${y}" r="8" fill="#ffffff" stroke="#132b4f" stroke-width="1.5"/>
      <circle cx="${x}" cy="${y}" r="3.5" fill="#132b4f"/>
      <text x="${x + 10}" y="${y + 4}" fill="#24313a" font-size="11">${escapeSvg(shortRegion(region))}</text>
    </g>
  `).join("");
  const listRows = waste.slice(0, 5).map((row, index) => {
    const y = 116 + index * 36;
    return `
      <g class="map-list">
        <text x="500" y="${y}">${escapeSvg(truncate(row.assigned_worker || "Worker", 18))}</text>
        <text x="500" y="${y + 15}" fill="#59636b">${escapeSvg(truncate(row.job_name || "Project", 27))}</text>
        <text x="700" y="${y + 6}" text-anchor="end" fill="#8f271d">${Number(row.avoidable_minutes_one_way || 0).toFixed(0)}m</text>
      </g>
    `;
  }).join("");
  const afterLayer = state.analysisRun
    ? `
      <g opacity="0.95">
        <path d="M198 326 C243 342, 318 319, 348 270" fill="none" stroke="#247c53" stroke-width="4" stroke-linecap="round"/>
        <text x="178" y="352" fill="#247c53" font-size="12" font-weight="700">Go-forward: local qualified coverage first, executive exceptions second</text>
        ${Object.values(REGION_POINTS).map(([x, y]) => `<circle cx="${x}" cy="${y}" r="13" fill="none" stroke="#247c53" stroke-width="2" opacity="0.75"/>`).join("")}
      </g>
    `
    : `<text x="176" y="352" fill="#45616d" font-size="12" font-weight="700">Run ML review to overlay the recommended coverage pattern</text>`;
  container.innerHTML = `
    <svg class="route-svg" viewBox="0 0 760 390" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <rect x="0" y="0" width="760" height="390" fill="transparent"/>
      <text x="26" y="31" fill="#33424d" font-size="13" font-weight="700">SWFL staffing command map</text>
      <text x="500" y="31" fill="#33424d" font-size="13" font-weight="700">Current long-haul conflicts</text>
      <text x="500" y="57" fill="#657078" font-size="11">One-way avoidable drive minutes on imported plan</text>
      <path d="M292 28 C338 72, 351 112, 335 151 C320 189, 340 226, 307 263 C281 293, 263 323, 215 348 C214 306, 204 270, 186 231 C166 188, 169 146, 189 104 C209 62, 239 40, 292 28 Z" fill="#eef1ec" stroke="#62727d" stroke-width="2"/>
      <path d="M188 104 C206 137, 207 172, 194 205 C185 228, 203 258, 211 297" fill="none" stroke="#8c9aa3" stroke-width="1.5" stroke-dasharray="5 6"/>
      <path d="M338 152 C363 163, 377 181, 378 207" fill="none" stroke="#8c9aa3" stroke-width="1.5" stroke-dasharray="5 6"/>
      ${conflictLines}
      ${regionNodes}
      ${afterLayer}
      <rect x="486" y="78" width="242" height="230" fill="#ffffff" stroke="#737373"/>
      <text x="500" y="101" fill="#8f271d" font-size="12" font-weight="700">Worst current leaks</text>
      ${listRows}
    </svg>
  `;
}

function renderLeafletRouteMap(waste, container) {
  const baselineLookup = Object.fromEntries((state.data.baseline || []).map((row) => [row.assignment_id, row]));
  const workerLookup = Object.fromEntries((state.data.workers || []).map((row) => [row.personnel_id, row]));
  const jobLookup = Object.fromEntries((state.data.jobsites || []).map((row) => [row.jobsite_id, row]));
  const conflicts = waste.map((row, index) => {
    const assignment = baselineLookup[row.assignment_id] || {};
    const worker = workerLookup[row.assigned_personnel] || workerLookup[assignment.personnel_id] || {};
    const closer = workerLookup[row.closer_qualified_worker] || {};
    const job = jobLookup[row.jobsite_id] || {};
    return {
      row,
      index,
      worker,
      closer,
      job,
      home: latLngFromWorker(worker, assignment.home_region),
      closerHome: latLngFromWorker(closer, assignment.home_region),
      jobPoint: latLngFromJob(job, assignment.job_region || row.job_region || row.job_name)
    };
  }).filter((item) => item.home && item.jobPoint);
  const now = new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  const tickerRows = conflicts.slice(0, 6).map(({ row }, index) => `
    <div class="map-ticker-row">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <strong>${escapeHtml(truncate(row.assigned_worker || "Worker", 20))}</strong>
      <small>${escapeHtml(truncate(row.job_name || "Project", 30))}</small>
      <b>${Number(row.avoidable_minutes_one_way || 0).toFixed(0)}m</b>
    </div>
  `).join("");
  container.innerHTML = `
    <div class="dispatch-map-shell">
      <div class="dispatch-map-windowbar">
        <strong>SWFL_DEPLOYMENT.EXE</strong>
        <span>${state.analysisRun ? "ML REVIEW COMPLETE" : "READ ONLY IMPORT"}</span>
      </div>
      <div class="dispatch-map" id="dispatchMap" aria-label="Interactive Southwest Florida staffing conflict map"></div>
      <aside class="dispatch-map-panel" aria-label="Live staffing review feed">
        <div class="map-panel-head">
          <span class="live-dot"></span>
          <div>
            <strong>${state.analysisRun ? "ML reviewed" : "Live staffing board"}</strong>
            <small>${now} demo feed</small>
          </div>
        </div>
        <div class="map-stats">
          <div><span>Conflicts</span><strong>${(state.data.waste || []).length}</strong></div>
          <div><span>Long-haul key staff</span><strong>${state.analysisRun ? "0" : Math.round(Number(state.economics.baseline_long_haul_key_staff || 27))}</strong></div>
          <div><span>Recovered/day</span><strong>${state.analysisRun ? `${Number(state.economics.route_hours_recovered || 0).toFixed(0)}h` : "--"}</strong></div>
        </div>
        <div class="map-ticker">${tickerRows}</div>
      </aside>
    </div>
  `;
  dispatchMap = L.map("dispatchMap", {
    zoomControl: false,
    scrollWheelZoom: false,
    attributionControl: true
  });
  L.control.zoom({ position: "bottomright" }).addTo(dispatchMap);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    subdomains: "abcd",
    maxZoom: 18,
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
  }).addTo(dispatchMap);
  const bounds = [];
  const maxMinutes = Math.max(...conflicts.map(({ row }) => Number(row.avoidable_minutes_one_way || 0)), 1);
  conflicts.forEach((conflict) => {
    const avoidable = Number(conflict.row.avoidable_minutes_one_way || 0);
    const intensity = Math.max(0.35, avoidable / maxMinutes);
    bounds.push(conflict.home, conflict.jobPoint);
    L.polyline([conflict.home, conflict.jobPoint], {
      color: conflict.index < 3 ? "#ff4d35" : "#ff9a3d",
      weight: 2 + intensity * 5,
      opacity: state.analysisRun ? 0.42 : 0.78,
      dashArray: conflict.index < 3 ? null : "9 8"
    }).addTo(dispatchMap);
    L.circleMarker(conflict.home, {
      radius: 4,
      color: "#d8e5ee",
      weight: 1,
      fillColor: "#111827",
      fillOpacity: 0.95
    }).addTo(dispatchMap);
    L.marker(conflict.jobPoint, {
      icon: pulseIcon(conflict.index < 3 ? "danger" : "warning")
    }).addTo(dispatchMap).bindPopup(`<strong>${escapeHtml(conflict.row.job_name || "Project")}</strong><br>${escapeHtml(conflict.row.assigned_worker || "Worker")} current conflict<br>${avoidable.toFixed(0)} min avoidable one-way`);
    if (state.analysisRun && conflict.closerHome) {
      bounds.push(conflict.closerHome);
      L.polyline([conflict.closerHome, conflict.jobPoint], {
        color: "#35d07f",
        weight: 3,
        opacity: 0.86
      }).addTo(dispatchMap);
      L.circleMarker(conflict.closerHome, {
        radius: 5,
        color: "#35d07f",
        weight: 2,
        fillColor: "#07140d",
        fillOpacity: 0.95
      }).addTo(dispatchMap);
    }
  });
  const legend = L.control({ position: "topleft" });
  legend.onAdd = () => {
    const node = L.DomUtil.create("div", "map-legend");
    node.innerHTML = `
      <strong>SWFL deployment layer</strong>
      <span><i class="legend-red"></i> Current long-haul conflict</span>
      <span><i class="legend-green"></i> ML go-forward coverage</span>
    `;
    return node;
  };
  legend.addTo(dispatchMap);
  if (bounds.length) {
    dispatchMap.fitBounds(bounds, { padding: [24, 24], maxZoom: 10 });
  } else {
    dispatchMap.setView([26.55, -81.82], 9);
  }
  setTimeout(() => dispatchMap?.invalidateSize(), 80);
}

function renderWeights() {
  const labels = {
    commute_reduction: "Travel load",
    skill_fit: "Role fit",
    certification_strictness: "OSHA / certs",
    supervisor_balance: "Superintendent load",
    retention_protection: "Burden risk",
    crew_cohesion: "Team continuity",
    overtime_reduction: "Load balance",
    robotics_utilization: "Remote capture",
    job_urgency: "Lookahead risk"
  };
  const weights = state.data.weights || [];
  const html = weights.map((row) => {
    const value = Number(row.value || 0);
    const width = Math.max(8, Math.min(100, (value / 1.85) * 100));
    return `
      <div class="signal-row">
        <span>${labels[row.weight] || row.weight}</span>
        <div class="signal-track"><i style="width:${width}%"></i></div>
        <strong>${value.toFixed(2)}</strong>
      </div>
    `;
  }).join("");
  document.getElementById("weightSignals").innerHTML = html || `<div class="empty-state">No recommended weights found.</div>`;
}

function renderRecommendations() {
  const list = document.getElementById("recommendationList");
  const recommendations = (state.data.recommendations || []).slice(0, 14);
  const filtered = recommendations.filter((row) => {
    const decision = state.decisions[row.recommendation_id] || "pending";
    return state.filter === "all" || decision === state.filter;
  });
  updateDecisionCounts(recommendations);
  if (!filtered.length) {
    list.innerHTML = `<div class="empty-state">No recommendations match this filter.</div>`;
    return;
  }
  list.innerHTML = filtered.map((row) => recommendationCard(row)).join("");
  list.querySelectorAll("[data-decision]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.recId;
      state.decisions[id] = button.dataset.decision;
      saveDecisions(state.decisions);
      renderRecommendations();
      renderMobilePreview();
    });
  });
}

function recommendationCard(row) {
  const id = row.recommendation_id;
  const decision = state.decisions[id] || "pending";
  return `
    <article class="recommendation-card">
      <div>
        <h3>${escapeHtml(row.worker_name)} → ${escapeHtml(row.job_name)}</h3>
        <p>${escapeHtml(formatReason(row.reason))}</p>
        <div class="rec-meta">
          <span>${escapeHtml(row.home_region)} to ${escapeHtml(row.job_region)}</span>
          <span>${Number(row.commute_minutes || 0).toFixed(0)} min travel load</span>
          <span>${percent(Number(row.skill_match_score || 0))} role fit</span>
          <span>${percent(Number(row.certification_match_score || 0))} OSHA/cert match</span>
        </div>
      </div>
      <div class="decision-actions" aria-label="Decision actions for ${escapeHtml(id)}">
        <button class="action-button approve ${decision === "approved" ? "is-selected" : ""}" type="button" data-rec-id="${escapeHtml(id)}" data-decision="approved">Approve</button>
        <button class="action-button review ${decision === "review" ? "is-selected" : ""}" type="button" data-rec-id="${escapeHtml(id)}" data-decision="review">Review</button>
        <button class="action-button reject ${decision === "rejected" ? "is-selected" : ""}" type="button" data-rec-id="${escapeHtml(id)}" data-decision="rejected">Reject</button>
      </div>
    </article>
  `;
}

function renderMobilePreview() {
  const recommendations = state.data.recommendations || [];
  const approved = recommendations.find((row) => state.decisions[row.recommendation_id] === "approved") || recommendations[0];
  const mobile = document.getElementById("mobilePreview");
  if (!approved) {
    mobile.innerHTML = `<div class="phone-card"><p>No assignment packet loaded.</p></div>`;
    return;
  }
  mobile.innerHTML = `
    <div class="phone-card">
      <span class="status-pill warning">Review item</span>
      <h3>${escapeHtml(approved.job_name)}</h3>
      <p>${escapeHtml(approved.worker_name)} is recommended after role fit, OSHA/cert coverage, travel load, project phase, and lookahead constraints.</p>
      <div class="phone-metric">
        <span>${Number(approved.commute_minutes || 0).toFixed(0)} min drive</span>
        <span>${percent(Number(approved.skill_match_score || 0))} role</span>
        <span>${percent(Number(approved.certification_match_score || 0))} OSHA/cert</span>
        <span>${money(Number(approved.estimated_daily_route_cost || 0))}/day</span>
      </div>
    </div>
    <div class="phone-card">
      <strong>Project leadership reason</strong>
      <p>${escapeHtml(formatReason(approved.reason))}</p>
    </div>
    <div class="phone-card">
      <strong>Required action</strong>
      <p>Approve the move, flag an infeasible constraint, or send an override reason back to operations.</p>
    </div>
  `;
}

function renderExports() {
  document.getElementById("exportGrid").innerHTML = EXPORTS.map(([label, file, caption]) => `
    <a class="export-card" href="${EXPORT_BASE}${file}" download>
      <strong>${label}</strong>
      <small>${caption}</small>
    </a>
  `).join("");
}

function updateDecisionCounts(recommendations) {
  const counts = { approved: 0, rejected: 0, review: 0 };
  recommendations.forEach((row) => {
    const decision = state.decisions[row.recommendation_id];
    if (counts[decision] !== undefined) {
      counts[decision] += 1;
    }
  });
  setText("approvedCount", String(counts.approved));
  setText("rejectedCount", String(counts.rejected));
  setText("reviewCount", String(counts.review));
}

async function fetchCsv(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return parseCsv(await response.text());
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (quoted) {
      if (char === "\"" && next === "\"") {
        value += "\"";
        index += 1;
      } else if (char === "\"") {
        quoted = false;
      } else {
        value += char;
      }
    } else if (char === "\"") {
      quoted = true;
    } else if (char === ",") {
      row.push(value);
      value = "";
    } else if (char === "\n") {
      row.push(value);
      rows.push(row);
      row = [];
      value = "";
    } else if (char !== "\r") {
      value += char;
    }
  }
  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }
  const headers = rows.shift() || [];
  return rows
    .filter((item) => item.some((cell) => cell !== ""))
    .map((item) => Object.fromEntries(headers.map((header, index) => [header, item[index] ?? ""])));
}

function routeHours(rows = []) {
  return sum(rows, "commute_minutes") * 2 / 60;
}

function deriveEconomics(deltaHours) {
  const e = state.economics || {};
  if (Number(e.annual_deployment_run_rate || 0) > 0) {
    return {
      annualRunRate: Number(e.annual_deployment_run_rate || 0),
      implementationImpact: Number(e.implementation_horizon_impact || 0),
      profitLeverage: Number(e.profit_leverage_pct || 0),
      leaks: [
        ["Retention / rehiring", e.retention_value, `${Number(e.retained_key_staff || 0).toFixed(1)} expected key-staff quits avoided`],
        ["Management capacity", e.route_capacity_value, `${Number(e.route_hours_recovered || 0).toFixed(1)} hrs/day returned from travel load`],
        ["Coverage gaps", e.coverage_value, `${Number(e.coverage_gap_reduction || 0).toFixed(0)} open slots closed`],
        ["Role / OSHA fit", Number(e.role_fit_value || 0) + Number(e.certification_value || 0), "rework and safety-coverage drag reduced"],
        ["Schedule variance", e.schedule_variance_value, "lookahead and constraint-log friction reduced"],
        ["QA / rework / closeout", Number(e.rework_value || 0) + Number(e.qa_closeout_value || 0), "inspection, punch, turnover proof tightened"],
        ["CO / admin drag", e.co_admin_value, "PCO/COR follow-up and PM admin friction reduced"],
        ["Margin fade", e.margin_fade_value, "gain/fade leakage from bad handoffs reduced"],
        ["Admin bandwidth", e.admin_operating_model_value, "HR backfill, recruiting fire drills, and staffing-meeting load reduced"],
        ["Compounding effect", e.compounding_value, `${percent(Number(e.compounding_factor || 0))} downstream waste multiplier avoided`]
      ]
    };
  }
  const annualRunRate = deltaHours * 77 * 250;
  return {
    annualRunRate,
    implementationImpact: annualRunRate * 1.5,
    profitLeverage: annualRunRate / (704000000 * 0.041),
    leaks: [["Management capacity", annualRunRate, `${deltaHours.toFixed(1)} hrs/day returned from travel load`]]
  };
}

function renderLeakGrid(economics) {
  const grid = document.getElementById("leakGrid");
  if (!grid) {
    return;
  }
  if (!state.analysisRun) {
    grid.innerHTML = `<div class="empty-state">Run ML staffing review to see the organizational leak model.</div>`;
    return;
  }
  grid.innerHTML = economics.leaks.map(([label, value, note]) => `
    <article class="leak-item">
      <span>${escapeHtml(label)}</span>
      <strong>${money(Number(value || 0))}</strong>
      <small>${escapeHtml(note)}</small>
    </article>
  `).join("");
}

function regionPoint(region, fallbackIndex = 0) {
  const label = String(region || "");
  if (REGION_POINTS[label]) {
    return REGION_POINTS[label];
  }
  const match = Object.keys(REGION_POINTS).find((name) => {
    const tokens = name.toLowerCase().split(/[-\s/]+/).filter((token) => token.length > 3);
    return tokens.some((token) => label.toLowerCase().includes(token));
  });
  return match ? REGION_POINTS[match] : FALLBACK_POINTS[fallbackIndex % FALLBACK_POINTS.length];
}

function conflictPath(from, to, index) {
  if (Math.abs(from[0] - to[0]) < 4 && Math.abs(from[1] - to[1]) < 4) {
    return `M ${from[0]} ${from[1]} C ${from[0] - 42} ${from[1] - 24}, ${from[0] + 36} ${from[1] - 36}, ${to[0] + 7} ${to[1] + 5}`;
  }
  const midX = (from[0] + to[0]) / 2;
  const midY = (from[1] + to[1]) / 2;
  const bend = index % 2 === 0 ? -36 : 34;
  return `M ${from[0]} ${from[1]} C ${midX + bend} ${midY - 48}, ${midX - bend} ${midY + 38}, ${to[0]} ${to[1]}`;
}

function shortRegion(region) {
  return String(region || "")
    .replace("Sarasota-Punta Gorda", "Sarasota / PG")
    .replace("Lehigh-Immokalee", "Lehigh / Immokalee");
}

function truncate(value, length) {
  const text = String(value || "");
  return text.length > length ? `${text.slice(0, Math.max(0, length - 1))}...` : text;
}

function resetDispatchMap() {
  if (dispatchMap) {
    dispatchMap.remove();
    dispatchMap = null;
  }
}

function latLngFromWorker(worker, fallbackRegion) {
  const lat = Number(worker.home_lat);
  const lon = Number(worker.home_lon);
  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    return [lat, lon];
  }
  return regionLatLng(fallbackRegion);
}

function latLngFromJob(job, fallbackRegion) {
  const lat = Number(job.lat);
  const lon = Number(job.lon);
  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    return [lat, lon];
  }
  return regionLatLng(fallbackRegion);
}

function regionLatLng(region) {
  const label = String(region || "");
  if (REGION_COORDS[label]) {
    return REGION_COORDS[label];
  }
  const match = Object.keys(REGION_COORDS).find((name) => {
    const tokens = name.toLowerCase().split(/[-\s/]+/).filter((token) => token.length > 3);
    return tokens.some((token) => label.toLowerCase().includes(token));
  });
  return match ? REGION_COORDS[match] : [26.55, -81.82];
}

function pulseIcon(level) {
  return L.divIcon({
    className: "pulse-icon-wrap",
    html: `<span class="pulse-marker ${level}"></span>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13]
  });
}

function sum(rows, key) {
  return rows.reduce((total, row) => total + Number(row[key] || 0), 0);
}

function boolish(value) {
  return value === true || value === "True" || value === "true" || value === "1";
}

function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(Number(value || 0));
}

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function formatReason(reason) {
  const text = String(reason || "");
  const driveMatch = text.match(/^Drove ([\d.]+) minutes despite qualified project staff within ([\d.]+) minutes\.$/);
  if (driveMatch) {
    return `Current plan creates a ${Number(driveMatch[1]).toFixed(0)}-minute drive where qualified project staff is available within ${Number(driveMatch[2]).toFixed(0)} minutes.`;
  }
  return text.replace("Optimizer selected", "AMDEP selected");
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function setSync(value) {
  setText("syncStatus", value);
}

function loadDecisions() {
  try {
    return JSON.parse(localStorage.getItem(DECISION_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveDecisions(decisions) {
  localStorage.setItem(DECISION_KEY, JSON.stringify(decisions));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeSvg(value) {
  return escapeHtml(value);
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.getRegistrations()
      .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
      .then(() => {
        if (!("caches" in window)) {
          return undefined;
        }
        return caches.keys().then((keys) => Promise.all(keys.map((key) => caches.delete(key))));
      })
      .catch(() => undefined);
  }
}
