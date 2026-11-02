# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Odoo 18.0 ERP system for Estevez.Jor, deployed via Docker Compose. The stack is: Odoo 18.0 + PostgreSQL 15 + pgAdmin.

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs in real time
docker-compose logs -f

# Restart all containers
docker-compose restart

# Stop without destroying volumes
docker-compose stop

# Access Odoo at http://localhost:8069
# pgAdmin at http://localhost:5050
```

**Updating modules after code changes:**

The container entrypoint already passes `-u` for the core custom modules and `--dev xml` (which auto-reloads XML without restart). For Python model changes, restart the container:

```bash
docker-compose restart odoo
```

To update a specific module manually:
```bash
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf -u <module_name>
```

## Production Deployment (differs from local)

- Production is a **GCP Compute Engine VM** running Odoo from a Python venv under **systemd** (`odoo18` service, user `odoo18`), not Docker.
- **Every push to `main` deploys to production** (`.github/workflows/deploy-erp.yml`): SSH → `git pull` in `/opt/odoo18/odoo-erp-docker` → `rsync` (no `--delete`) of `custom_addons/` into `/opt/odoo18/odoo-erp/custom-addons/` → `systemctl restart odoo18`.
- The workflow does **not** back up the database and does **not** run `-u`, so new fields, data files, QWeb/XML views and migration scripts are not applied by the deploy itself (unless the systemd unit's `ExecStart` passes `-u` — unverified). Only Python-only and static-asset changes are safe to push to `main` today.
- **Top priority: infrastructure modernization** — spec in [docs/infra/spec.md](docs/infra/spec.md) (GCE + Docker Compose + Cloud SQL, immutable images, backup + `-u` + health check on every deploy). Start every infra session at its section "0. Retomar aquí". No other change that touches the schema or XML ships until its phase 4 is done.
- Work that is ready but blocked by the deploy is parked as patches in `docs/wip/` (outside `custom_addons/`, so `rsync` does not ship it); apply with `git apply`.

## Running Tests

Odoo tests run inside the container against a test database:

```bash
# Run tests for a specific module
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf --test-enable --stop-after-init -u hr_estevez

# Run a single test class
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf --test-enable --stop-after-init -u hr_estevez --test-tags TestHrDirection
```

Tests inherit from `odoo.tests.common.TransactionCase`. See `custom_addons/hr_estevez/tests/test_hr_direction.py` for the pattern used.

**Prefer an isolated test database** over `odoo-prod` (the `db_name` in `config/odoo.conf`). Create it once with `-i`, then use `-u`. Use a separate `--http-port` so `HttpCase` does not clash with the running server:

```bash
# MSYS_NO_PATHCONV=1 is required from Git Bash on Windows; otherwise /etc/odoo/... becomes a Windows path
MSYS_NO_PATHCONV=1 docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf \
  -d test_<module> -i <module> --test-enable --test-tags /<module> \
  --stop-after-init --http-port 8079 --log-level=test
```

Then grep the log for `ERROR|FAIL:|tests when loading`. `HttpCase` classes must be tagged `post_install, -at_install` and run after the `TransactionCase` ones.

## Development Workflow (SDD + TDD)

New work and refactors follow spec-driven + test-driven development:

1. **Spec first** — each module being refactored keeps `docs/spec.md` with: purpose/scope, architecture decisions (`D1…`), acceptance criteria with IDs (`<MOD>-NN`, Given/When/Then), and a traceability table (criterion → test → ✅/🔴/⏳) with the date of the last run.
2. **Red** — write tests that cite the criterion ID in the docstring; run them and record which fail.
3. **Green / refactor** — implement, keep tests green, update the traceability table and the module README.
4. Bugs found by tests go in the spec's "Hallazgos" section.

Test conventions: test against public interfaces (Settings `create(...).execute()`, HTTP routes) so tests survive refactors; shared helpers live in `tests/common.py`; tag classes with the module name.

### Refactor status

| Module | Spec | Status |
|---|---|---|
| Infrastructure | [docs/infra/spec.md](docs/infra/spec.md) | Spec written; nothing built. Next: phase 0 (manual prod backup + gather the data in section 7). |
| auth_estevez | [docs/spec.md](custom_addons/auth_estevez/docs/spec.md) | Step 1 (spec + tests) on `main`: 4/15 green — red tests are the pending spec. Step 2 (backend on `res.company` + migration `18.0.2.0.0`) validated at 13/15 but **parked** in `docs/wip/auth_estevez-paso2-backend.patch`, blocked by infra INFRA-07/08. Steps 3 (QWeb) and 4 (assets) follow. |

### Odoo 18 pitfalls seen in this repo

- A `default=` on a `res.config.settings` field with `config_parameter=` only applies inside the Settings form; code that reads the parameter directly gets `None` on a fresh database.
- Do not mutate `odoo.addons.web.controllers.home.SIGN_UP_REQUEST_PARAMS` or write config into `request.params`; extend the response with `response.qcontext.update(...)` after `super()`.
- `check_access_rights` is deprecated in 18 — use `check_access`.
- Store settings that need defaults, validation or images as `res.company` fields exposed in Settings via `related=..., readonly=False` — not as base64 in `ir.config_parameter`. Serve images with `request.env['ir.binary']._get_image_stream_from(record, field, placeholder=...)`.
- Restarting the `odoo` container runs `-u` on `odoo-prod` for the modules in the entrypoint, so **migration scripts run on restart**. Back up first.
- Migration scripts (`migrations/<version>/post-migrate.py`) are testable: load them with `importlib.util.spec_from_file_location` and call `migrate(cr, version)` (see `auth_estevez/tests/test_migration.py`).
- Anything in `web.assets_frontend` applies to the portal, eLearning and website too; scope CSS under a module root class. `web.assets_frontend` already includes `web._assets_bootstrap_frontend`.

## Repository Structure

```
custom_addons/    # Estevez.Jor custom modules (primary development area)
third_party_addons/  # External addons (muk_web_*, themes, login_as_any_user, etc.)
addons/           # Odoo core addons (not modified directly)
config/           # odoo.conf
Dockerfile        # Extends odoo:18.0, adds pandas, xlsxwriter, holidays
docker-compose.yml
```

## Custom Addons

The modules listed in the docker-compose entrypoint (`-u` flag) are auto-updated on container start:
- **hr_estevez** — Core HR: employees, contracts, memorandums, loans, leaves, vacations, org structure (directions/areas)
- **auth_estevez** — Custom login page UI and password toggle (under SDD/TDD refactor — see `docs/spec.md`)
- **menu_estevez** — Menu visibility customizations
- **hr_attendance_controls_adv** — Third-party advanced attendance controls (base for hr_attendance_estevez)
- **hr_recruitment_estevez** — Recruitment extensions: requisitions, driving tests, applicant documents
- **hr_attendance_estevez** — Attendance overrides with payroll/attendance XLSX reports (uses pandas)

Other custom modules (not in the auto-update list — must be updated manually when changed):
- **hr_incapacity** — Employee medical incapacity management
- **custom_training_extension** — Training catalogs and employee-course relationships
- **elearning_estevez** — eLearning course form customizations
- **hr_elearning_integration** — HR ↔ eLearning: course certificates, employee course view
- **profile_estevez** — User profile page customizations
- **roles_permissions_estevez** — Default user roles and access rights
- **email_templates_estevez** — Custom reset-password email template
- **google_meet_estevez** — Google Meet links on calendar events
- **custom_inputs_estevez** — Global UI: custom input styles, spinner, PWA manifest/icons
- **base_user_role** / **base_menu_visibility_restriction** — OCA modules for roles and menu control
- **report_xlsx** / **report_xlsx_helper** — OCA XLSX report engine (used by hr_attendance_estevez)

## Addon Structure Convention

Every custom addon follows the standard Odoo layout:

```
<module>/
  __manifest__.py       # Module metadata and data file list (order matters)
  __init__.py
  models/               # Python model classes (inherit or extend Odoo models)
  views/                # XML views, menus, actions
  report/               # QWeb report actions (*_report.xml) and templates (*_report_templates.xml)
  security/             # ir.model.access.csv and security group XML
  data/                 # Default data, cron jobs
  static/src/           # JS, SCSS, XML components (OWL framework)
  i18n/                 # Translation .po files (es.po, es_419.po)
  tests/                # TransactionCase test classes
  migrations/           # Version migration scripts (pre/post-migrate.py)
```

## Report Development

Reports come in pairs:
- `*_report.xml` — defines `ir.actions.report` (report action and paper format)
- `*_report_templates.xml` — defines the QWeb `<template>` with actual HTML/CSS layout

`hr_report_common_layout_templates.xml` in `hr_estevez/report/` defines the shared layout (header, footer, company logo) inherited by all HR reports via `t-call`.

XLSX reports (attendance/payroll) use the `report_xlsx` OCA module — the report class inherits from `AbstractReportXlsx` instead of QWeb.

## Key Model Hierarchy

`hr_estevez` introduces an org structure above standard Odoo HR:
- `hr.direction` → `hr.department` (department has a `direction_id` FK)
- `hr.area` — sub-level below department
- `hr.employee` is extended with: direction, area, job history, document attachments, loans, memorandums, vacation periods, time-off in lieu

## Environment Variables

A `.env` file (not committed) must define:
```
ODOO_PORT, ODOO_LONGPOLLING_PORT
DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
PG_ADMIN_EMAIL, PG_ADMIN_PASSWORD
ADMIN_PASSWORD
```
