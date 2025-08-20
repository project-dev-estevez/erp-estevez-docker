/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DashboardHeader } from "./dashboard_header/dashboard_header.js";
import { KpisGrid } from "./kpis/kpis_grid.js";
import { ChartRendererApex } from "./chart_renderer_apex/chart_renderer_apex.js";
import { chartsDummy } from "./chart_renderer_apex/charts_dummy.js";

export class EmployeesDashboard extends Component {
    static template = "hr_estevez.EmployeesDashboard";
    static components = { DashboardHeader, KpisGrid, ChartRendererApex };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().slice(0, 10);
        this.state = useState({
            totalEmployees: 0,
            activeEmployees: 0,
            inactiveEmployees: 0,
            newEmployeesThisMonth: 0,
            departmentData: [],
            areaData: [],
            upcomingBirthdays: [],
            contractsExpiring: [],
            contractStats: {
                fixed: 0,
                indefinite: 0,
                temporary: 0
            },
            loading: true,
            startDate: firstDay,
            endDate: lastDay
        });

    this.chartsDummy = chartsDummy;

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    onDateChange = (startDate, endDate) => {
        this.state.startDate = startDate;
        this.state.endDate = endDate;
        this.loadDashboardData();
    }

    async loadDashboardData() {
        try {
            // ...existing code...
        } catch (error) {
            // ...existing code...
        }
    }
    // ...existing code...
}

registry.category("actions").add("hr_estevez.EmployeesDashboard", EmployeesDashboard);
