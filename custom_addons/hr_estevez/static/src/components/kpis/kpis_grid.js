/** @odoo-module **/
import { Component } from "@odoo/owl";
import { KpiCard } from "./kpi_card/kpi_card.js";

export class KpisGrid extends Component {
    static template = "hr_estevez.KpisGrid";
    static components = { KpiCard };
}
