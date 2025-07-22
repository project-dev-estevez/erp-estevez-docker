/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { DashboardHeader } from "./dashboard_header/dashboard_header";
import { KpisGrid } from "./kpis/kpis_grid";
import { RecruiterEfficiencyChart } from "./charts/recruiter_efficiency_chart/recruiter_efficiency_chart";
import { ProcessEfficiencyChart } from "./charts/process_efficiency_chart/process_efficiency_chart";
import { RecruitmentSourcesChart } from "./charts/recruitment_sources_chart/recruitment_sources_chart";
import { RejectionReasonsChart } from "./charts/rejection_reasons_chart/rejection_reasons_chart";
import { RecruitmentFunnelChart } from "./charts/recruitment_funnel_chart/recruitment_funnel_chart";
import { RequisitionStatsChart } from "./charts/requisition_stats_chart/requisition_stats_chart";

export class RecruitmentDashboard extends Component {

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        // 🔗 Referencias de componentes
        this.kpisGridComponent = null;
        this.recruiterEfficiencyComponent = null;
        this.processEfficiencyComponent = null;
        this.recruitmentSourcesComponent = null;
        this.rejectionReasonsComponent = null;
        this.recruitmentFunnelComponent = null;
        this.requisitionStatsComponent = null;

        this.state = useState({
            startDate: "",
            endDate: ""
        });

        // ✅ Inicializar dashboard
        onWillStart(async () => {
            this.initializeDateRange();
        });
    }

    // 📅 ============ GESTIÓN DE FECHAS ============
    initializeDateRange() {
        const today = new Date();
        const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        this.state.startDate = firstDayOfMonth.toISOString().split('T')[0];
        this.state.endDate = today.toISOString().split('T')[0];
    }

    _addDateRangeToDomain(domain = []) {
        if (this.state.startDate) {
            domain.push(["create_date", ">=", this.state.startDate]);
        }
        if (this.state.endDate) {
            domain.push(["create_date", "<=", this.state.endDate]);
        }
        return domain;
    }

    _getHiredDateRangeDomain(domain = []) {
        if (this.state.startDate) {
            domain.push(["date_closed", ">=", this.state.startDate]);
        }
        if (this.state.endDate) {
            domain.push(["date_closed", "<=", this.state.endDate]);
        }
        return domain;
    }

    // 🔗 ============ CALLBACKS DE MONTAJE ============
    onKpisGridMounted(kpisGridComponent) {
        console.log("📊 Dashboard: KpisGrid montado");
        this.kpisGridComponent = kpisGridComponent;
    }

    onRecruiterEfficiencyMounted(recruiterEfficiencyComponent) {
        console.log("📊 Dashboard: RecruiterEfficiencyChart montado");
        this.recruiterEfficiencyComponent = recruiterEfficiencyComponent;
    }

    onProcessEfficiencyMounted(processEfficiencyComponent) {
        console.log("📊 Dashboard: ProcessEfficiencyChart montado");
        this.processEfficiencyComponent = processEfficiencyComponent;
    }

    onRecruitmentSourcesMounted(recruitmentSourcesComponent) {
        console.log("📊 Dashboard: RecruitmentSourcesChart montado");
        this.recruitmentSourcesComponent = recruitmentSourcesComponent;
    }

    onRejectionReasonsMounted(rejectionReasonsComponent) {
        console.log("📊 Dashboard: RejectionReasonsChart montado");
        this.rejectionReasonsComponent = rejectionReasonsComponent;
    }

    onRecruitmentFunnelMounted(recruitmentFunnelComponent) {
        console.log("📊 Dashboard: RecruitmentFunnelChart montado");
        this.recruitmentFunnelComponent = recruitmentFunnelComponent;
    }

    onRequisitionStatsMounted(requisitionStatsComponent) {
        console.log("📊 Dashboard: RequisitionStatsChart montado");
        this.requisitionStatsComponent = requisitionStatsComponent;
    }

    // 🔄 ============ ACTUALIZACIÓN DE FECHAS ============
    async onDateRangeChange(startDate, endDate) {
        console.log("📅 Dashboard: Actualizando rango de fechas:", { startDate, endDate });
        
        this.state.startDate = startDate;
        this.state.endDate = endDate;
        
        // ✅ Recargar todos los componentes en paralelo
        const reloadPromises = [];
        
        // 📊 KPIs
        if (this.kpisGridComponent) {
            reloadPromises.push(this.kpisGridComponent.loadKpisData());
        }

        // 📈 Gráficos
        if (this.recruiterEfficiencyComponent) {
            reloadPromises.push(this.recruiterEfficiencyComponent.loadChartData());
        }

        if (this.processEfficiencyComponent) {
            reloadPromises.push(this.processEfficiencyComponent.refresh());
        }

        if (this.recruitmentSourcesComponent) {
            reloadPromises.push(this.recruitmentSourcesComponent.refresh());
        }

        if (this.rejectionReasonsComponent) {
            reloadPromises.push(this.rejectionReasonsComponent.refresh());
        }

        if (this.recruitmentFunnelComponent) {
            reloadPromises.push(this.recruitmentFunnelComponent.refresh());
        }

        if (this.requisitionStatsComponent) {
            reloadPromises.push(this.requisitionStatsComponent.refresh());
        }
        
        // ⏳ Esperar todas las recargas
        await Promise.all(reloadPromises);
        
        console.log("✅ Dashboard: Todos los componentes actualizados");
    }

    // 🔍 ============ NAVEGACIÓN A LISTAS ============
    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false) {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);
        domain.push(["user_id", "=", userId]);

        // ✅ Filtros específicos
        if (onlyHired) {
            domain.push(["application_status", "=", "hired"]);
        } else if (onlyOngoing) {
            domain.push(["application_status", "=", "ongoing"]);
        }

        const actionName = onlyHired ? 'Contratados' : 
                          onlyOngoing ? 'En Proceso' : 
                          'Postulaciones';

        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: actionName,
            res_model: 'hr.applicant',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { active_test: false },
        });
    }

    async openRequisitionList(stateCode) {
        let domain = [];
        domain = this._addDateRangeToDomain(domain);
        
        if (stateCode === 'approved_open') {
            domain.push(['state', '=', 'approved'], ['is_published', '=', true]);
        } else if (stateCode === 'approved_closed') {
            domain.push(['state', '=', 'approved'], ['is_published', '=', false]);
        } else if (stateCode) {
            domain.push(['state', '=', stateCode]);
        }
        
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Requisiciones',
            res_model: 'hr.requisition',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
        });
    }

    // 🎨 ============ UTILIDADES ============
    getPastelColors(count) {
        const premiumColors = [
            '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB347',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#FF6B6B',
        ];

        if (count <= premiumColors.length) {
            return premiumColors.slice(0, count);
        }

        const colors = [...premiumColors];
        
        for (let i = premiumColors.length; i < count; i++) {
            const hue = Math.floor((360 / (count - premiumColors.length)) * (i - premiumColors.length));
            const saturation = 65 + Math.random() * 20;
            const lightness = 55 + Math.random() * 20;
            colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }
        
        return colors;
    }
}

// 🎯 ============ CONFIGURACIÓN DEL COMPONENTE ============
RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = {
    DashboardHeader, 
    KpisGrid, 
    RecruiterEfficiencyChart,
    ProcessEfficiencyChart, 
    RecruitmentSourcesChart,
    RejectionReasonsChart, 
    RecruitmentFunnelChart,
    RequisitionStatsChart
};

// 📝 Registrar el dashboard
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);