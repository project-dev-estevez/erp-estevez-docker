/** @odoo-module **/
import { Component, onWillStart } from "@odoo/owl";
import { KpiCard } from "./kpi_card/kpi_card.js";
import { KpiChartCard } from "./kpi_chart_card/kpi_chart_card.js";

export class KpisGrid extends Component {
    static template = "hr_estevez.KpisGrid";
    static components = { KpiCard, KpiChartCard };

    setup() {
        this.state = {
            totalEmployees: 0,
            totalSeries: [],
            activeEmployees: 0,
            inactiveEmployees: 0,
        };
        onWillStart(async () => {
            try {
                const orm = this.env.services.orm;
                // Total empleados
                const context = { context: { active_test: false } };
                const total = await orm.searchCount("hr.employee", [], context);
                const active = await orm.searchCount("hr.employee", [["active", "=", true]]);
                const inactive = await orm.searchCount("hr.employee", [["active", "=", false]], context);

                // Serie para la gráfica de total empleados (últimos 7 días)
                const today = new Date();
                let totalSeries = [];
                for (let i = 6; i >= 0; i--) {
                    const date = new Date(today);
                    date.setDate(today.getDate() - i);
                    const dateStr = date.toISOString().slice(0, 10);
                    const count = await orm.searchCount("hr.employee", [["create_date", ">=", dateStr + " 00:00:00"], ["create_date", "<=", dateStr + " 23:59:59"]]);
                    totalSeries.push(count);
                }

                this.state.totalEmployees = total;
                this.state.totalSeries = totalSeries;
                this.state.activeEmployees = active;
                this.state.inactiveEmployees = inactive;
            } catch (error) {
                console.error("Error cargando KPIs de empleados:", error);
            }
        });
    }
}
