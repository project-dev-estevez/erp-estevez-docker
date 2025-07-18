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

import { ChartRenderer } from "./chart_renderer/chart_renderer";

export class RecruitmentDashboard extends Component {

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        // ✅ Variables para referencias de componentes
        this.kpisGridComponent = null;
        this.recruiterEfficiencyComponent = null;
        this.processEfficiencyComponent = null;
        this.recruitmentSourcesComponent = null;
        this.rejectionReasonsComponent = null;
        this.recruitmentFunnelComponent = null;
        this.requisitionStatsComponent = null;

        this.state = useState({
            // Filtros
            startDate: "",
            endDate: "",
            requisitionStats: {},
        });

        // ✅ Cargar datos al inicializar
        onWillStart(async () => {
            // Inicializar fechas por defecto
            const today = new Date();
            const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            this.state.startDate = firstDayOfMonth.toISOString().split('T')[0];
            this.state.endDate = today.toISOString().split('T')[0];

            // Cargar datos del dashboard (sin KPIs)
            await this.loadAllData();
        });
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

    // ✅ Callbacks de montaje de componentes
    onKpisGridMounted(kpisGridComponent) {
        console.log("📊 Dashboard: KpisGrid montado", kpisGridComponent);
        this.kpisGridComponent = kpisGridComponent;
    }

    onRecruiterEfficiencyMounted(recruiterEfficiencyComponent) {
        console.log("📊 Dashboard: RecruiterEfficiencyChart montado", recruiterEfficiencyComponent);
        this.recruiterEfficiencyComponent = recruiterEfficiencyComponent;
    }

    onProcessEfficiencyMounted(processEfficiencyComponent) {
        console.log("📊 Dashboard: ProcessEfficiencyChart montado", processEfficiencyComponent);
        this.processEfficiencyComponent = processEfficiencyComponent;
    }

    onRecruitmentSourcesMounted(recruitmentSourcesComponent) {
        console.log("📊 Dashboard: RecruitmentSourcesChart montado", recruitmentSourcesComponent);
        this.recruitmentSourcesComponent = recruitmentSourcesComponent;
    }

    openRejectionDetails = (reason) => {
        // Ejemplo: mostrar modal con detalles
        this.setState({
            showRejectionModal: true,
            selectedReason: reason
        });
        
        // O cargar datos relacionados:
        // fetchCandidatesByReason(reason.id).then(data => {...})
    }

    onRejectionReasonsMounted(rejectionReasonsComponent) {
        console.log("📊 Dashboard: RejectionReasonsChart montado", rejectionReasonsComponent);
        this.rejectionReasonsComponent = rejectionReasonsComponent;
    }

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

    onRecruitmentFunnelMounted(recruitmentFunnelComponent) {
        console.log("📊 Dashboard: RecruitmentFunnelChart montado", recruitmentFunnelComponent);
        this.recruitmentFunnelComponent = recruitmentFunnelComponent;
    }

    onRequisitionStatsMounted(requisitionStatsComponent) {
        console.log("📊 Dashboard: RequisitionStatsChart montado", requisitionStatsComponent);
        this.requisitionStatsComponent = requisitionStatsComponent;
    }

    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false) {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);

        domain.push(["user_id", "=", userId]);

        // ✅ NUEVO: Filtrar por tipo de aplicación
        if (onlyHired) {
            domain.push(["application_status", "=", "hired"]);
        } else if (onlyOngoing) {
            domain.push(["application_status", "=", "ongoing"]);
        }

        let actionName = 'Postulaciones';
        if (onlyHired) {
            actionName = 'Contratados';
        } else if (onlyOngoing) {
            actionName = 'En Proceso';
        }

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
        views: [[false,'list'],[false,'form']],
        domain: domain,
        });
    }

    async onDateRangeChange(startDate, endDate) {
        
        this.state.startDate = startDate;
        this.state.endDate = endDate;
        
        // ✅ CREAR array para promises de recarga
        const reloadPromises = [];
        
        if (this.kpisGridComponent) {
            reloadPromises.push(this.kpisGridComponent.loadKpisData());
        }

        if (this.recruiterEfficiencyComponent) {
            reloadPromises.push(this.recruiterEfficiencyComponent.loadChartData());
        }

        if (this.processEfficiencyComponent) {
            reloadPromises.push(this.processEfficiencyComponent.refresh());
        }

        if (this.recruitmentSourcesComponent) {
            console.log("🔄 Dashboard: Recargando fuentes de reclutamiento...");
            reloadPromises.push(this.recruitmentSourcesComponent.refresh());
        }

        if (this.rejectionReasonsComponent) {
            console.log("🔄 Dashboard: Recargando motivos de rechazo...");
            reloadPromises.push(this.rejectionReasonsComponent.refresh());
        }

        if (this.recruitmentFunnelComponent) {
            console.log("🔄 Dashboard: Recargando embudo de reclutamiento...");
            reloadPromises.push(this.recruitmentFunnelComponent.refresh());
        }

        if (this.requisitionStatsComponent) {
            console.log("🔄 Dashboard: Recargando estadísticas de requisiciones...");
            reloadPromises.push(this.requisitionStatsComponent.refresh());
        }
        
        // ✅ ESPERAR todas las recargas en paralelo
        await Promise.all(reloadPromises);
        
        // Recargar datos de gráficos del dashboard
        await this.loadAllData();
    }

    async loadAllData() {
        try {
            await Promise.all([
                this.getRequisitionStats(),
            ]);
            console.log("✅ Dashboard: Todos los datos cargados");
        } catch (error) {
            console.error("❌ Dashboard: Error cargando datos:", error);
        }
    }

    async getRequisitionStats() {
        let domain = [];
        domain = this._addDateRangeToDomain(domain);
    
        const data = await this.orm.readGroup(
            'hr.requisition',
            domain,
            ['state'],
            ['state']
        );
        //Convertir a un map
        const countMap = {};
        data.forEach(r => {
          countMap[r.state] = r.state_count;
        });
        //Definir labels y conteos en orden
        const labels = [
          'Total',
          'Por Activar',  // to_approve
          'Abiertas',     // approved & is_published = true
          'Cerradas'      // approved & is_published = false
        ];
        // Total = suma de todos
        const total = data.reduce((sum, r) => sum + r.state_count, 0);
        // Contar cada estado
        const countToApprove = countMap['to_approve'] || 0;
        const countApprovedOpen = await this.orm.searchCount(
          'hr.requisition',
          [...domain, ['state', '=', 'approved'], ['is_published', '=', true]]
        );
        const countApprovedClosed = await this.orm.searchCount(
          'hr.requisition',
          [...domain, ['state', '=', 'approved'], ['is_published', '=', false]]
        );

        const meta = [
          { state: null },               // para “Total”
          { state: 'to_approve' },
          { state: 'approved_open' },    // código interno
          { state: 'approved_closed' },
        ];
        const counts = [
          total,
          countToApprove,
          countApprovedOpen,
          countApprovedClosed,
        ];
    
        this.state.requisitionStats = {
          data: {
            labels,
            datasets: [{
              label: 'Requisiciones',
              data: counts,
              backgroundColor: this.getPastelColors(labels.length),
            }]
          },
          meta,
          options: {
            indexAxis: 'x',
            scales: {
                x: {
                  beginAtZero: true,
                  ticks: { autoSkip: false }
                },
                y: {
                  beginAtZero: true,
                },
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        generateLabels: chart => {
                            // labels[] = ['Total','Por Activar','Abiertas','Cerradas']
                            // backgroundColor[] = color por cada barra
                            const data = chart.data;
                            return data.labels.map((lbl, i) => ({
                                text: lbl,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                hidden: chart.getDataVisibility(i) === false,
                                index: i,
                            }));
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${labels[ctx.dataIndex]}: ${counts[ctx.dataIndex]}`
                    }
                }
            },
            onClick: (event, active) => {
              if (!active.length) return;
              const idx = active[0].index;
              const item = this.state.requisitionStats.meta[idx];
              this.openRequisitionList(item.state);
            },
            plugins: {
              tooltip: {
                callbacks: {
                  label: ctx => `${labels[ctx.dataIndex]}: ${counts[ctx.dataIndex]}`
                }
              }
            }
          }
        };
        // fuerza el update
        this.state.requisitionStats = { ...this.state.requisitionStats };
    }

}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = {
    DashboardHeader, KpisGrid, 
    ChartRenderer, RecruiterEfficiencyChart,
    ProcessEfficiencyChart, RecruitmentSourcesChart,
    RejectionReasonsChart, RecruitmentFunnelChart,
    RequisitionStatsChart
};

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);