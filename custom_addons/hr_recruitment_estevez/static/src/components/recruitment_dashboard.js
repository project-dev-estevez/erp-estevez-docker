/** @odoo-module **/

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card/kpi_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
const { DateTime } = luxon;

export class RecruitmentDashboard extends Component {

    getPastelColors(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = Math.floor((360 / count) * i + Math.random() * 30);
            colors.push(`hsl(${hue}, 70%, 85%)`);
        }
        return colors;
    }

    async getTopRecruitments() {
        const domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.readGroup("hr.applicant", domain, ["user_id"], ["user_id"]);

        this.state.topRecruitments = {
            data: {
                labels: data.map(item => item.user_id[1] || "Desconocido"),
                datasets: [
                    {
                        label: "Postulaciones",
                        data: data.map(item => item.user_id_count),
                        backgroundColor: this.getPastelColors(data.length)
                    }
                ]
            }
        };
    }

    async getSourceRecruitment() {
        const domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["source_id"],
            ["source_id"]
        );

        // Procesamiento de datos más robusto
        const sourcesData = data.map(r => ({
            label: (r.source_id && r.source_id[1]) || "Sin fuente",
            count: r.source_id_count,
            sourceId: r.source_id ? r.source_id[0] : null
        }));

        this.state.sourceRecruitment = {
            data: {
                labels: sourcesData.map(item => item.label),
                datasets: [
                    {
                        label: "Fuentes de Postulación",
                        data: sourcesData.map(item => item.count),
                        backgroundColor: this.getPastelColors(sourcesData.length)
                    }
                ]
            }
        };
    }

    setup() {
        this.state = useState({
            // Postulaciones Totales
            totalApplicants: {
                value: 0,
                percentage: 0,
            },
            // Postulaciones En Progreso
            inProgressApplicants: {
                value: 0,
                percentage: 0,
            },
            // Candidatos Preseleccionados
            preselectedApplicants: {
                value: 0,
                percentage: 0,
            },
            // Postulaciones Rechazadas
            rejectedApplicants: {
                value: 0,
                percentage: 0,
            },
            // Contrataciones Realizadas
            hiredApplicants: {
                value: 0,
                percentage: 0,
            },
            // Tiempo promedio de contratación
            averageHiringTime: {
                value: 0,
                previousValue: 0,
            },
            period: 30,
            currentDate: DateTime.now().minus({ days: 30 }).toISODate(),
            previusDate: DateTime.now().minus({ days: 60 }).toISODate()
        })

        this.orm = useService("orm");
        this.actionservice = useService("action");

        onWillStart(async () => {
            await this.getTopRecruitments();
            await this.getSourceRecruitment();
            await this.onPeriodChange();
        });
    }

    getDates() {
        this.state.currentDate = DateTime.now().minus({ days: this.state.period }).toISODate();
        this.state.previusDate = DateTime.now().minus({ days: this.state.period * 2 }).toISODate();
    }

    async onPeriodChange() {
        this.getDates();

        await Promise.all([
            this.getTotalApplicants(),
            this.getInProgressApplicants(),
            this.getPreselectedApplicants(),
            this.getRejectedApplicants(),
            this.getHiredApplicants(),
            this.getAverageHiringTime()
        ]);
    }

    async getTotalApplicants() {
        const context = { context: { active_test: false } };
        let domain = [];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.totalApplicants.value = data;

        // Periodo previo
        let previousDomain = [];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }
        const previousData = await this.orm.searchCount("hr.applicant", previousDomain, context);
        const percentage = ((data - previousData) / previousData) * 100;
        this.state.totalApplicants.percentage = percentage.toFixed(2) || 0;
    }

    async getInProgressApplicants() {
        let domain = [["application_status", "=", "ongoing"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.inProgressApplicants.value = data;

        // Periodo previo
        let previousDomain = [["application_status", "=", "ongoing"]];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }
        const previousData = await this.orm.searchCount("hr.applicant", previousDomain);
        const percentage = ((data - previousData) / previousData) * 100;
        this.state.inProgressApplicants.percentage = percentage.toFixed(2) || 0;
    }

    async getPreselectedApplicants() {
        // Buscar applicants cuya etapa (stage_id.sequence) sea mayor a 4
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.preselectedApplicants.value = data;

        // Periodo previo
        let previousDomain = [
            ["stage_id.sequence", ">", 4], 
            ["application_status", "!=", "hired"]
        ];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }
        const previousData = await this.orm.searchCount("hr.applicant", previousDomain);
        const percentage = ((data - previousData) / previousData) * 100;
        this.state.preselectedApplicants.percentage = percentage.toFixed(2) || 0;
    }

    async getRejectedApplicants() {
        const context = { context: { active_test: false } };
        let domain = [["application_status", "=", "refused"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.rejectedApplicants.value = data;

        // Periodo previo
        let previousDomain = [["application_status", "=", "refused"]];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }
        const previousData = await this.orm.searchCount("hr.applicant", previousDomain, context);
        const percentage = ((data - previousData) / previousData) * 100;
        this.state.rejectedApplicants.percentage = percentage.toFixed(2) || 0;
    }

    async getHiredApplicants() {
        let domain = [["application_status", "=", "hired"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.hiredApplicants.value = data;

        // Periodo previo
        let previousDomain = [["application_status", "=", "hired"]];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }
        const previousData = await this.orm.searchCount("hr.applicant", previousDomain);
        const percentage = ((data - previousData) / previousData) * 100;
        this.state.hiredApplicants.percentage = percentage.toFixed(2) || 0;
    }

    async getAverageHiringTime() {
        let domain = [["application_status", "=", "hired"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const applicants = await this.orm.searchRead('hr.applicant', domain, ["create_date", "date_closed"]);
        if (!applicants.length) {
            return 0;
        }

        let totalDays = 0;
        let count = 0;
        for (const applicant of applicants) {
            if (applicant.create_date && applicant.date_closed) {
                const created = new Date(applicant.create_date);
                const closed = new Date(applicant.date_closed);
                const diffTime = closed - created;
                const diffDays = diffTime / (1000 * 60 * 60 * 24);
                totalDays += diffDays;
                count += 1;
            }
        }

        const averageDays = count ? (totalDays / count) : 0;
        this.state.averageHiringTime.value = averageDays.toFixed(2);

        // Periodo previo
        let previousDomain = [["application_status", "=", "hired"]];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }

        const previousApplicants = await this.orm.searchRead('hr.applicant', previousDomain, ["create_date", "date_closed"]);
        if (!previousApplicants.length) {
            return 0;
        }

        let previousTotalDays = 0;
        let previousCount = 0;
        for (const applicant of previousApplicants) {
            if (applicant.create_date && applicant.date_closed) {
                const created = new Date(applicant.create_date);
                const closed = new Date(applicant.date_closed);
                const diffTime = closed - created;
                const diffDays = diffTime / (1000 * 60 * 60 * 24);
                previousTotalDays += diffDays;
                previousCount += 1;
            }
        }
        const previousAverageDays = previousCount ? (previousTotalDays / previousCount) : 0;
        this.state.averageHiringTime.previousValue = previousAverageDays
            ? (((averageDays - previousAverageDays) / previousAverageDays) * 100).toFixed(2)
            : 0;
    }

    viewTotalApplicants() {
        const context = { active_test: false };
        let domain = [];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        this.actionservice.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: context,
        });
    }

    viewInProgressApplicants() {
        let domain = [["application_status", "=", "ongoing"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        this.actionservice.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones en Progreso",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
        });
    }

    viewPreselectedApplicants() {
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        this.actionservice.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones Preseleccionadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
        });
    }

    viewRejectedApplicants() {
        const context = { active_test: false };
        let domain = [["application_status", "=", "refused"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        this.actionservice.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones Rechazadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: context
        });
    }

    viewHiredApplicants() {
        let domain = [["application_status", "=", "hired"]];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        this.actionservice.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones Contratadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]]
        });
    }

    viewAverageHiringTime() {
        // No-op to avoid errors
        return;
    }

}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = { KpiCard, ChartRenderer };

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);