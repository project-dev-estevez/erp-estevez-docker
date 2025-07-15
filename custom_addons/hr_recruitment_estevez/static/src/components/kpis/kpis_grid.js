/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { KpiCard } from "./kpi_card/kpi_card";

export class KpisGrid extends Component {
    static template = "hr_recruitment_estevez.KpisGrid";
    static components = { KpiCard };
    static props = {
        kpisData: Object,
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
    };

    setup() {
        this.actionService = useService("action");
    }

    // ✅ Métodos de filtrado por fechas
    _addDateRangeToDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["create_date", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["create_date", "<=", this.props.endDate]);
        }
        return domain;
    }

    _getHiredDateRangeDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["date_closed", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["date_closed", "<=", this.props.endDate]);
        }
        return domain;
    }

    get kpis() {
        const { kpisData } = this.props;
        
        return [
            {
                name: "Postulaciones",
                value: kpisData.totalApplicants?.value || 0,
                percentage: kpisData.totalApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.viewTotalApplicants()
            },
            {
                name: "En Progreso",
                value: kpisData.inProgressApplicants?.value || 0,
                percentage: kpisData.inProgressApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.viewInProgressApplicants()
            },
            {
                name: "Preseleccionados",
                value: kpisData.preselectedApplicants?.value || 0,
                percentage: kpisData.preselectedApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.viewPreselectedApplicants()
            },
            {
                name: "Rechazados",
                value: kpisData.rejectedApplicants?.value || 0,
                percentage: kpisData.rejectedApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.viewRejectedApplicants()
            },
            {
                name: "Contratados",
                value: kpisData.hiredApplicants?.value || 0,
                percentage: kpisData.hiredApplicants?.percentage || null,
                showPercentage: false,
                onClick: () => this.viewHiredApplicants()
            },
            {
                name: "Tiempo Promedio",
                value: kpisData.averageHiringTime?.value || "0 días",
                percentage: kpisData.averageHiringTime?.previousValue || null,
                showPercentage: false,
                onClick: () => this.viewAverageHiringTime()
            }
        ];
    }

    // ✅ Métodos de navegación (MARAVILLA TOTAL 🚀)
    viewTotalApplicants() {
        console.log(`🎯 KpisGrid: ¡Navegando a postulaciones totales!`);
        const context = { active_test: false };
        let domain = [];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "📋 Todas las Postulaciones",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: context,
        });
    }

    viewInProgressApplicants() {
        console.log(`🔄 KpisGrid: ¡Navegando a postulaciones en progreso!`);
        let domain = [["application_status", "=", "ongoing"]];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "🔄 Postulaciones en Progreso",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
        });
    }

    viewPreselectedApplicants() {
        console.log(`⭐ KpisGrid: ¡Navegando a preseleccionados!`);
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "⭐ Candidatos Preseleccionados",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
        });
    }

    viewRejectedApplicants() {
        console.log(`❌ KpisGrid: ¡Navegando a rechazados!`);
        const context = { active_test: false };
        let domain = [["application_status", "=", "refused"]];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "❌ Postulaciones Rechazadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: context
        });
    }

    viewHiredApplicants() {
        console.log(`✅ KpisGrid: ¡Navegando a contratados!`);
        let domain = [["application_status", "=", "hired"]];
        domain = this._getHiredDateRangeDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "✅ Candidatos Contratados",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]]
        });
    }

    viewAverageHiringTime() {
        console.log(`⏱️ KpisGrid: ¡Mostrando análisis de tiempo!`);
        
        // ✅ Opción premium: mostrar historial de etapas
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "⏱️ Análisis de Tiempo de Contratación",
            res_model: "hr.applicant.stage.history",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ['applicant_id.application_status', '=', 'hired'],
                ['leave_date', '!=', false]
            ],
            context: {
                search_default_group_by_stage: 1,
                search_default_group_by_applicant: 1
            }
        });
    }
}