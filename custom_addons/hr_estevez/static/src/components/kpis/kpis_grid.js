/** @odoo-module **/
import { Component } from "@odoo/owl";
import { KpiCard } from "./kpi_card/kpi_card.js";
import { KpiChartCard } from "./kpi_chart_card/kpi_chart_card.js";

export class KpisGrid extends Component {
    static template = "hr_estevez.KpisGrid";
    static components = { KpiCard, KpiChartCard };
}
