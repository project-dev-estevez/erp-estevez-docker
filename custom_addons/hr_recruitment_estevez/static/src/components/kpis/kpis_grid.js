/** @odoo-module **/

import { Component } from "@odoo/owl";
import { KpiCard } from "./kpi_card/kpi_card";

export class KpisGrid extends Component {
    static template = "hr_recruitment_estevez.KpisGrid";
    static components = { KpiCard };
    static props = {
        kpisData: Object,                // Datos de todos los KPIs
        onKpiClick: { 
            type: Function, 
            optional: true 
        },                               // Función para manejar clicks
    };

    // ✅ Configuración de KPIs con sus propiedades
    get kpis() {
        const { kpisData } = this.props;
        
        return [
            {
                name: "Postulaciones",
                value: kpisData.totalApplicants?.value || 0,
                percentage: kpisData.totalApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.handleKpiClick("viewTotalApplicants")
            },
            {
                name: "En Progreso",
                value: kpisData.inProgressApplicants?.value || 0,
                percentage: kpisData.inProgressApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.handleKpiClick("viewInProgressApplicants")
            },
            {
                name: "Preseleccionados",
                value: kpisData.preselectedApplicants?.value || 0,
                percentage: kpisData.preselectedApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.handleKpiClick("viewPreselectedApplicants")
            },
            {
                name: "Rechazados",
                value: kpisData.rejectedApplicants?.value || 0,
                percentage: kpisData.rejectedApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.handleKpiClick("viewRejectedApplicants")
            },
            {
                name: "Contratados",
                value: kpisData.hiredApplicants?.value || 0,
                percentage: kpisData.hiredApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.handleKpiClick("viewHiredApplicants")
            },
            {
                name: "Tiempo Promedio",
                value: kpisData.averageHiringTime?.value || "0 días",
                percentage: kpisData.averageHiringTime?.previousValue || null,
                showPercentage: false,
                onClick: () => this.handleKpiClick("viewAverageHiringTime")
            }
        ];
    }

    // ✅ Manejar clicks en KPIs
    handleKpiClick(action) {
        console.log(`📊 KPI clicked: ${action}`);
        if (this.props.onKpiClick) {
            this.props.onKpiClick(action);
        }
    }
}