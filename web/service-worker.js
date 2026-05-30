const CACHE_NAME = "amdep-demo-v6";

const APP_SHELL = [
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./assets/amdep-mark.svg",
  "./demo-data.json",
  "../docs/DEMO_METHODOLOGY_AND_DEPLOYMENT.md",
  "../reports/demo_audit/baseline_assignments.csv",
  "../reports/demo_audit/optimized_assignments.csv",
  "../reports/demo_audit/top_waste_findings.csv",
  "../reports/demo_audit/personnel_burden.csv",
  "../reports/demo_audit/job_staffing_status.csv",
  "../reports/demo_audit/robotics_plan.csv",
  "../reports/demo_audit/calibration_trials.csv",
  "../reports/demo_audit/recommended_weights.csv",
  "../reports/demo_audit/integrations/recommendations_generic.csv"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => undefined)
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy)).catch(() => undefined);
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
