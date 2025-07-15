/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class RecruiterEfficiencyChart extends Component {
    static template = "hr_recruitment_estevez.RecruiterEfficiencyChart";
    static components = { ChartRendererApex };
    static props = {
        chartData: Object,
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
        title: { type: String, optional: true },
        height: { type: [String, Number], optional: true },
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

    get chartTitle() {
        return this.props.title || "Eficiencia por Reclutador";
    }

    get chartHeight() {
        return this.props.height || 350;
    }

    // ✅ Navegar a postulaciones del reclutador
    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false) {
        console.log(`🎯 RecruiterChart: Navegando a postulaciones del reclutador ${userId}`);
        
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);
        domain.push(["user_id", "=", userId]);

        // ✅ Filtrar por tipo de aplicación
        if (onlyHired) {
            domain.push(["application_status", "=", "hired"]);
        } else if (onlyOngoing) {
            domain.push(["application_status", "=", "ongoing"]);
        }

        let actionName = 'Postulaciones del Reclutador';
        if (onlyHired) {
            actionName = 'Contratados del Reclutador';
        } else if (onlyOngoing) {
            actionName = 'En Proceso del Reclutador';
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
}