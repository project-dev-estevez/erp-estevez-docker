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

## Running Tests

Odoo tests run inside the container against a test database:

```bash
# Run tests for a specific module
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf --test-enable --stop-after-init -u hr_estevez

# Run a single test class
docker-compose exec odoo odoo -c /etc/odoo/odoo.conf --test-enable --stop-after-init -u hr_estevez --test-tags TestHrDirection
```

Tests inherit from `odoo.tests.common.TransactionCase`. See `custom_addons/hr_estevez/tests/test_hr_direction.py` for the pattern used.

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
- **auth_estevez** — Custom login page UI and password toggle
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
