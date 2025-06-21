/** @odoo-module **/

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card/kpi_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
const { DateTime } = luxon;

export class RecruitmentDashboard extends Component {

    _addDateRangeToDomain(domain = []) {
        if (this.state.startDate) {
            domain.push(["create_date", ">=", this.state.startDate]);
        }
        if (this.state.endDate) {
            domain.push(["create_date", "<=", this.state.endDate]);
        }
        return domain;
    }

    setup() {
        const now = DateTime.now();
        const startOfMonth = now.startOf('month').toISODate();
        const endOfMonth = now.endOf('month').toISODate();

        this.state = useState({
            // Postulaciones Totales
            totalApplicants: {
                value: 0,
            },
            // Postulaciones En Progreso
            inProgressApplicants: {
                value: 0,
            },
            // Candidatos Preseleccionados
            preselectedApplicants: {
                value: 0,
            },
            // Postulaciones Rechazadas
            rejectedApplicants: {
                value: 0,
            },
            // Contrataciones Realizadas
            hiredApplicants: {
                value: 0,
            },
            // Tiempo promedio de contratación
            averageHiringTime: {
                value: 0,
            },
            // Fuentes de Reclutamiento
            sourceRecruitment: {},
            indicatorsSourceRecruitment: {
                sources: []
            },

            startDate: startOfMonth,
            endDate: endOfMonth,
        })

        this.orm = useService("orm");
        this.actionservice = useService("action");

        onWillStart(async () => {
            await this.loadAllData();
        });
    }

    onDateRangeChange() {
        if (this.state.startDate && this.state.endDate && this.state.endDate < this.state.startDate) {
            // Corrige automáticamente o muestra un mensaje
            this.state.endDate = this.state.startDate;
        }
        this.loadAllData();        
    }

    async loadAllData() {        
        await Promise.all([
            this.getTopRecruitments(),
            this.getSourceRecruitment(),
            this.getIndicatorsSourceRecruitment(),
            this.getTotalApplicants(),
            this.getInProgressApplicants(),
            this.getPreselectedApplicants(),
            this.getRejectedApplicants(),
            this.getHiredApplicants(),
            this.getAverageHiringTime()
        ]);
    }

    getPastelColors(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = Math.floor((360 / count) * i + Math.random() * 30);
            colors.push(`hsl(${hue}, 70%, 85%)`);
        }
        return colors;
    }

    async getTopRecruitments() {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        domain = this._addDateRangeToDomain(domain);

        // Total postulaciones por reclutador
        const totalData = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        // Solo contratados por reclutador
        const hiredDomain = [
            ...domain,
            ["application_status", "=", "hired"]
        ];
        const hiredData = await this.orm.readGroup(
            "hr.applicant",
            hiredDomain,
            ["user_id"],
            ["user_id"]
        );

        const hiredMap = {};
        for (const r of hiredData) {
            const key = (r.user_id && r.user_id[1]) || "Desconocido";
            hiredMap[key] = r.user_id_count;
        }

        // Calcula porcentaje y prepara datos para tooltip
        const recruiterStats = totalData.map(r => {
            const label = (r.user_id && r.user_id[1]) || "Desconocido";
            const total = r.user_id_count;
            const hired = hiredMap[label] || 0;
            const percentage = total > 0 ? ((hired / total) * 100).toFixed(2) : "0.00";
            return { label, total, hired, percentage };
        });

        // Si no hay datos, asegúrate de pasar arrays vacíos
        const labels = recruiterStats.length ? recruiterStats.map(r => r.label) : [];
        const totalCounts = recruiterStats.length ? recruiterStats.map(r => r.total) : [];
        const hiredCounts = recruiterStats.length ? recruiterStats.map(r => r.hired) : [];


        this.state.topRecruitments = {
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Total Postulaciones",
                        data: totalCounts,
                        backgroundColor: "hsl(210, 70%, 85%)"
                    },
                    {
                        label: "Contratados",
                        data: hiredCounts,
                        backgroundColor: "hsl(140, 70%, 85%)"
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterBody: (context) => {
                                const idx = context[0].dataIndex;
                                const stat = recruiterStats[idx];
                                return `Porcentaje de contratación: ${stat.percentage}%`;
                            }
                        }
                    }
                }
            }
        };

        // Forzar refresco
        this.state.topRecruitments = { ...this.state.topRecruitments };
    }

    async getSourceRecruitment() {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["source_id"],
            ["source_id"]
        );

        const sourcesData = data.map(r => ({
            label: (r.source_id && r.source_id[1]) || "Sin fuente",
            count: r.source_id_count,
            sourceId: r.source_id ? r.source_id[0] : null
        }));

        // Si no hay datos, asegúrate de pasar arrays vacíos
        const labels = sourcesData.length ? sourcesData.map(item => item.label) : [];
        const counts = sourcesData.length ? sourcesData.map(item => item.count) : [];
        const colors = sourcesData.length ? this.getPastelColors(sourcesData.length) : [];

        this.state.sourceRecruitment = {
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Fuentes de Postulación",
                        data: counts,
                        backgroundColor: colors
                    }
                ]
            }
        };
        // Forzar refresco
        this.state.sourceRecruitment = { ...this.state.sourceRecruitment };
    }

    async getIndicatorsSourceRecruitment() {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        domain = this._addDateRangeToDomain(domain);

        // 1. Agrupa por source_id para obtener el total de candidatos por fuente
        const totalData = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["source_id"],
            ["source_id"]
        );

        // 2. Agrupa por source_id solo los contratados
        const hiredDomain = [
            ...domain,
            ["application_status", "=", "hired"]
        ];
        const hiredData = await this.orm.readGroup(
            "hr.applicant",
            hiredDomain,
            ["source_id"],
            ["source_id"]
        );

        // 3. Indexa los contratados por source_id para fácil acceso
        const hiredMap = {};
        for (const r of hiredData) {
            const key = (r.source_id && r.source_id[1]) || "Sin fuente";
            hiredMap[key] = r.source_id_count;
        }

        // 4. Construye el array de indicadores
        const indicators = totalData.map(r => {
            const label = (r.source_id && r.source_id[1]) || "Sin fuente";
            const total = r.source_id_count;
            const hired = hiredMap[label] || 0;
            const percentage = total > 0 ? ((hired / total) * 100).toFixed(2) : "0.00";
            return { label, total, hired, percentage };
        });

        // 5. Guarda en el estado
        this.state.indicatorsSourceRecruitment.sources = indicators;

    }

    async getTotalApplicants() {
        const context = { context: { active_test: false } };
        let domain = [];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.totalApplicants.value = data;
    }

    async getInProgressApplicants() {
        let domain = [["application_status", "=", "ongoing"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.inProgressApplicants.value = data;
    }

    async getPreselectedApplicants() {
        // Buscar applicants cuya etapa (stage_id.sequence) sea mayor a 4
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.preselectedApplicants.value = data;
    }

    async getRejectedApplicants() {
        const context = { context: { active_test: false } };
        let domain = [["application_status", "=", "refused"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.rejectedApplicants.value = data;
    }

    async getHiredApplicants() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.hiredApplicants.value = data;
    }

    async getAverageHiringTime() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._addDateRangeToDomain(domain);

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
    }

    viewTotalApplicants() {
        const context = { active_test: false };
        let domain = [];
        domain = this._addDateRangeToDomain(domain);

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
        domain = this._addDateRangeToDomain(domain);

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
        domain = this._addDateRangeToDomain(domain);

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
        domain = this._addDateRangeToDomain(domain);

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
        domain = this._addDateRangeToDomain(domain);

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