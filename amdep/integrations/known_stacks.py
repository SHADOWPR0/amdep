"""Known contractor-stack integration manifests.

These manifests are deliberately conservative. They describe import/export
contracts and implementation posture without pretending this public repo has
customer credentials or vendor partnership approval.
"""

from __future__ import annotations

from amdep.integrations.base import FieldMapping, StackManifest


KNOWN_STACKS: dict[str, StackManifest] = {
    "generic_csv": StackManifest(
        stack_id="generic_csv",
        display_name="Generic CSV / Excel / BI",
        category="universal",
        best_first_use="Fast audit from exported rosters, jobs, assignments, timecards, and equipment lists.",
        import_surfaces=("CSV", "Excel-exported CSV", "warehouse table"),
        export_surfaces=("recommendations CSV", "audit packet HTML", "Power BI / Tableau-ready CSV"),
        auth_model="none for file mode",
        data_notes="Best first path for most operators because it avoids procurement and API access friction.",
        field_mappings=(
            FieldMapping("Employee ID", "personnel_id", True),
            FieldMapping("Project / Job ID", "jobsite_id", True),
            FieldMapping("Project Address or Lat/Lon", "jobsite location", True),
            FieldMapping("Skills / Trade / Job Title", "skills", False),
            FieldMapping("Certifications", "certifications", False),
        ),
    ),
    "procore": StackManifest(
        stack_id="procore",
        display_name="Procore Resource Planning",
        category="construction workforce management",
        best_first_use="Pull workforce assignments and project/resource planning exports; return optimized assignment recommendations for operations approval.",
        import_surfaces=("Resource Planning assignments", "People list", "Projects", "Assignment list export", "API/sandbox"),
        export_surfaces=("Resource Planning recommendation CSV", "custom field update payload", "BI/reporting dataset"),
        auth_model="OAuth app through Procore developer sandbox or customer-authorized integration",
        data_notes="Procore Resource Planning exposes assignment concepts such as project, person, job title, dates, work hours, allocation, overtime, and project address.",
        field_mappings=(
            FieldMapping("Employee ID", "personnel_id", True),
            FieldMapping("Name / Person", "name", True),
            FieldMapping("Project", "jobsite_id", True),
            FieldMapping("Project Address / City / State / Postal", "jobsite location", True),
            FieldMapping("Job Title", "skills", False),
            FieldMapping("Start Date / End Date", "shift window", False),
            FieldMapping("Overtime", "overtime exposure", False),
        ),
        source_url="https://support.procore.com/products/online/user-guide/company-level/resource-planning/tutorials/view-the-resource-assignments-list",
    ),
    "servicetitan": StackManifest(
        stack_id="servicetitan",
        display_name="ServiceTitan",
        category="field service dispatch",
        best_first_use="Analyze jobs, appointments, technicians, skills, locations, shifts, and capacity; return appointment/technician reassignment recommendations.",
        import_surfaces=("Jobs API", "Appointments API", "Technicians", "Technician shifts", "Capacity", "Dispatch board exports"),
        export_surfaces=("appointment recommendation CSV", "technician reassignment payload draft", "operations review queue"),
        auth_model="ServiceTitan developer app and customer tenant authorization",
        data_notes="ServiceTitan distinguishes jobs, appointments, locations, technicians, shifts, and capacity. Some appointment/job transitions are constrained after invoices or timesheets exist.",
        field_mappings=(
            FieldMapping("technicianId", "personnel_id", True),
            FieldMapping("jobId", "jobsite_id", True),
            FieldMapping("appointmentId", "assignment_id", False),
            FieldMapping("location", "jobsite location", True),
            FieldMapping("businessUnit / jobType", "skills", False),
            FieldMapping("shift", "capacity window", False),
        ),
        source_url="https://developer.servicetitan.io/docs/api-resources-job-planning",
    ),
    "hcss_heavyjob": StackManifest(
        stack_id="hcss_heavyjob",
        display_name="HCSS HeavyJob",
        category="heavy civil field operations",
        best_first_use="Use timecards, foremen, jobs, employees, equipment, and missing timecard data to audit crew/equipment deployment.",
        import_surfaces=("HeavyJob timecards", "employee hours", "equipment hours", "foremen", "jobs", "business units"),
        export_surfaces=("crew/equipment recommendation CSV", "timecard variance dataset", "job-cost BI dataset"),
        auth_model="OAuth client with HeavyJob/timecard scopes",
        data_notes="HeavyJob APIs expose timecard summaries/details, employees, equipment, cost codes, foremen, and approval-related data.",
        field_mappings=(
            FieldMapping("employee.id", "personnel_id", True),
            FieldMapping("job.id / jobCode", "jobsite_id", True),
            FieldMapping("foreman.id", "supervisor_id", False),
            FieldMapping("equipment.id", "asset_id", False),
            FieldMapping("costCodes", "work phase / cost type", False),
        ),
        source_url="https://developer.hcssapps.com/hcss/docs/heavyjob-timecards",
    ),
    "sage_construction_management": StackManifest(
        stack_id="sage_construction_management",
        display_name="Sage Construction Management",
        category="construction accounting and project controls",
        best_first_use="Use projects, labor timecards, equipment timecards, job costs, and financials to score deployment waste against cost reality.",
        import_surfaces=("Projects", "Labor Timecards", "Equipment Timecards", "Job Cost Codes", "Project Financials"),
        export_surfaces=("labor/equipment recommendation CSV", "audit evidence dataset", "implementation-ready API payload draft"),
        auth_model="OAuth 2.0 or configured Sage Construction Management API keys",
        data_notes="Sage Construction Management APIs expose companies, projects, labor/equipment timecards, job costs, and project financials, with webhooks available for approved apps.",
        field_mappings=(
            FieldMapping("EMPLOYEEID", "personnel_id", True),
            FieldMapping("PROJECTID", "jobsite_id", True),
            FieldMapping("TASKID / COSTTYPEID", "work phase / cost type", False),
            FieldMapping("ENTRYDATE", "deployment_date", False),
            FieldMapping("QTY", "actual_hours", False),
        ),
        source_url="https://api-ext.sagecm.intacct.com/Documentation/GettingStarted",
    ),
    "trimble_vista": StackManifest(
        stack_id="trimble_vista",
        display_name="Trimble Viewpoint Vista",
        category="construction ERP",
        best_first_use="Pair ERP job/labor/equipment truth with AmDep optimization outputs for mid-to-large contractors.",
        import_surfaces=("Vista API", "job/labor/equipment exports", "operational reporting tables"),
        export_surfaces=("recommendation dataset", "ERP/BI reconciliation CSV", "audit packet"),
        auth_model="Trimble developer/API access through customer environment",
        data_notes="Vista is a construction ERP for project management and operational data; access depends on customer environment and Trimble configuration.",
        field_mappings=(
            FieldMapping("employee", "personnel_id", True),
            FieldMapping("job", "jobsite_id", True),
            FieldMapping("phase / cost type", "work phase", False),
            FieldMapping("equipment", "asset_id", False),
        ),
        source_url="https://developer.trimble.com/docs/vista/",
    ),
    "autodesk_construction_cloud": StackManifest(
        stack_id="autodesk_construction_cloud",
        display_name="Autodesk Construction Cloud",
        category="project data and construction workflows",
        best_first_use="Use project, issue, asset, form, and schedule-related data as context; return deployment recommendations to BI or workflow review.",
        import_surfaces=("Projects", "Issues", "Assets", "Forms", "Files", "Schedule exports"),
        export_surfaces=("deployment recommendation dataset", "issue/action import draft", "data lake / BI dataset"),
        auth_model="Autodesk Platform Services app with customer authorization",
        data_notes="ACC APIs are useful for project/workflow context. Workforce dispatch may still require CSV, ERP, or field-system data alongside ACC.",
        field_mappings=(
            FieldMapping("projectId", "jobsite_id", True),
            FieldMapping("project address / coordinates", "jobsite location", True),
            FieldMapping("issue type / form type", "work phase / risk", False),
            FieldMapping("assetId", "asset_id", False),
        ),
        source_url="https://forge.autodesk.com/developer/overview/autodesk-construction-cloud",
    ),
    "acculynx": StackManifest(
        stack_id="acculynx",
        display_name="AccuLynx",
        category="roofing operations",
        best_first_use="Roofing/storm restoration audit from jobs, appointments, crews, supplier/measurement context, and calendar/API exports.",
        import_surfaces=("AccuLynx API", "Zapier", "calendar sync", "job exports"),
        export_surfaces=("roofing production recommendation CSV", "Zapier-ready rows", "operations review queue"),
        auth_model="account API key or Zapier path depending on customer access",
        data_notes="AccuLynx supports API and Zapier integration paths; API access requires an active account and administrator-provided API key.",
        field_mappings=(
            FieldMapping("jobId", "jobsite_id", True),
            FieldMapping("contact / customer", "customer reference", False),
            FieldMapping("appointment / task", "assignment_id", False),
            FieldMapping("job address", "jobsite location", True),
            FieldMapping("crew / salesperson / production owner", "personnel_id", False),
        ),
        source_url="https://apidocs.acculynx.com/docs/overview",
    ),
}


def get_stack_manifest(stack_id: str) -> StackManifest:
    """Return a known stack manifest by id."""
    try:
        return KNOWN_STACKS[stack_id]
    except KeyError as exc:
        known = ", ".join(sorted(KNOWN_STACKS))
        raise KeyError(f"Unknown stack_id {stack_id!r}. Known stacks: {known}") from exc
