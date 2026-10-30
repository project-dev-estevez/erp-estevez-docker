/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { DashboardHeader } from "./dashboard_header/dashboard_header";
import { KpisGrid } from "./kpis/kpis_grid";
import { RecruitmentExecutive } from "./executive/recruitment_executive";

const { DateTime } = luxon;

export class RecruitmentDashboard extends Component {
    static template = "recruitment.dashboard";
    static components = { DashboardHeader, KpisGrid, RecruitmentExecutive };

    setup() {
        // 🔗 Referencia a las tarjetas para recargarlas al cambiar las fechas
        this.kpisGridComponent = null;

        this.state = useState({
            startDate: "",
            endDate: ""
        });

        onWillStart(async () => {
            this.initializeDateRange();
        });
    }

    // 📅 ============ GESTIÓN DE FECHAS ============
    initializeDateRange() {
        // Mes en curso en la zona horaria del usuario (toISOString daba mañana después de las 18:00 en México)
        const today = DateTime.local();
        this.state.startDate = today.startOf("month").toISODate();
        this.state.endDate = today.toISODate();
    }

    onKpisGridMounted(kpisGridComponent) {
        this.kpisGridComponent = kpisGridComponent;
    }

    // 🔄 ============ ACTUALIZACIÓN DE FECHAS ============
    async onDateRangeChange(startDate, endDate) {
        this.state.startDate = startDate;
        this.state.endDate = endDate;
        // La sección de desempeño se recarga sola al recibir las nuevas fechas por props
        if (this.kpisGridComponent) {
            await this.kpisGridComponent.loadKpisData();
        }
    }
}

// 📝 Registrar el dashboard
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);
