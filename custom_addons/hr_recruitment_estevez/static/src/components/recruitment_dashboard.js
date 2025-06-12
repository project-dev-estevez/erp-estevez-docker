/** @odoo-module **/

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card/kpi_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { Component } from "@odoo/owl";

export class RecruitmentDashboard extends Component {}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = { KpiCard, ChartRenderer };

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);