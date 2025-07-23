/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { KpiCard } from "./kpi_card/kpi_card";
import { PostulationsDetailModal } from "./modals/postulations_detail_modal";

export class KpisGrid extends Component {

    static template = "hr_recruitment_estevez.KpisGrid";
    static components = { KpiCard, PostulationsDetailModal };
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
        onMounted: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        // ✅ Estado local para los KPIs
        this.state = useState({
            totalApplicants: { value: 0 },
            inProgressApplicants: { value: 0 },
            preselectedApplicants: { value: 0 },
            rejectedApplicants: { value: 0 },
            hiredApplicants: { value: 0 },
            averageHiringTime: { value: "0 días" },
            isLoading: true,
            showModal: false
        });

        // ✅ Cargar datos cuando el componente se inicializa
        onWillStart(async () => {
            await this.loadKpisData();
        });

        // ✅ Notificar al componente padre cuando se monte
        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });
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

    // ✅ Getter para los KPIs (ahora usa el estado local)
    get kpis() {
        return [
            {
                name: "Postulaciones",
                value: this.state.totalApplicants.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewTotalApplicants()
            },
            {
                name: "En Progreso",
                value: this.state.inProgressApplicants.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewInProgressApplicants()
            },
            {
                name: "Preseleccionados",
                value: this.state.preselectedApplicants.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewPreselectedApplicants()
            },
            {
                name: "Rechazados",
                value: this.state.rejectedApplicants.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewRejectedApplicants()
            },
            {
                name: "Contratados",
                value: this.state.hiredApplicants.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewHiredApplicants()
            },
            {
                name: "Tiempo Promedio (Días)",
                value: this.state.averageHiringTime.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewAverageHiringTime()
            }
        ];
    }

    // ✅ Método principal para cargar todos los KPIs
    async loadKpisData() {
        console.log("📊 KpisGrid: Cargando datos de KPIs...");
        this.state.isLoading = true;
        
        try {
            await Promise.all([
                this.calculateTotalApplicants(),
                this.calculateInProgressApplicants(),
                this.calculatePreselectedApplicants(),
                this.calculateRejectedApplicants(),
                this.calculateHiredApplicants(),
                this.calculateAverageHiringTime(),
            ]);
            console.log("✅ KpisGrid: Datos cargados exitosamente");
        } catch (error) {
            console.error("❌ KpisGrid: Error cargando datos:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async calculateTotalApplicants() {
        try {
            // 1. ✅ Buscar la etapa "Primer contacto" (OBLIGATORIA)
            const primerContactoStage = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primer contacto']],
                ['id', 'name', 'sequence'],
                { limit: 1 }
            );

            if (!primerContactoStage.length) {
                this.state.totalApplicants.value = 0;
                return;
            }

            const primerContactoSequence = primerContactoStage[0].sequence;

            // 2. ✅ Contar candidatos que han SUPERADO "Primer contacto"
            let domain = [
                ['stage_id.sequence', '>', primerContactoSequence]
            ];
            domain = this._addDateRangeToDomain(domain);

            const count = await this.orm.searchCount(
                "hr.applicant", 
                domain, 
                { context: { active_test: false } }
            );

            this.state.totalApplicants.value = count;
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando Total Postulaciones:", error);
            this.state.totalApplicants.value = 0;
        }
    }

    async calculateInProgressApplicants() {
        try {
            // 1. ✅ Buscar la etapa "Primer contacto" (OBLIGATORIA)
            const primerContactoStage = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primer contacto']],
                ['id', 'name', 'sequence'],
                { limit: 1 }
            );

            if (!primerContactoStage.length) {
                console.error("❌ KpisGrid: Etapa 'Primer contacto' NO encontrada para En Progreso");
                this.state.inProgressApplicants.value = 0;
                return;
            }

            const primerContactoSequence = primerContactoStage[0].sequence;

            // 2. ✅ Contar candidatos que han superado "Primer contacto" 
            //    PERO que NO están rechazados ni contratados
            let domain = [
                ['stage_id.sequence', '>', primerContactoSequence],    // ✅ Después de primer contacto
                ['application_status', '!=', 'refused'],              // ✅ NO rechazados
                ['application_status', '!=', 'hired']                 // ✅ NO contratados
            ];
            domain = this._addDateRangeToDomain(domain);

            const count = await this.orm.searchCount("hr.applicant", domain);
            this.state.inProgressApplicants.value = count;
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando En Progreso:", error);
            this.state.inProgressApplicants.value = 0;
        }
    }

    async calculatePreselectedApplicants() {
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.preselectedApplicants.value = data;
        console.log("⭐ Preselected applicants:", data);
    }

    async calculateRejectedApplicants() {
        const context = { context: { active_test: false } };
        let domain = [["application_status", "=", "refused"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.rejectedApplicants.value = data;
        console.log("❌ Rejected applicants:", data);
    }

    async calculateHiredApplicants() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._getHiredDateRangeDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.hiredApplicants.value = data;
        console.log("✅ Hired applicants:", data);
    }

    async calculateAverageHiringTime() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._addDateRangeToDomain(domain);

        const applicants = await this.orm.searchRead('hr.applicant', domain, ["create_date", "date_closed"]);
        if (!applicants.length) {
            this.state.averageHiringTime.value = "0";
            return;
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
        this.state.averageHiringTime.value = `${averageDays.toFixed(1)}`;
        console.log("⏱️ Average hiring time:", `${averageDays.toFixed(1)} días`);
    }

    // ✅ Métodos de navegación
    async viewTotalApplicants() {
        this.state.showModal = true;
    }

    async viewInProgressApplicants() {
        try {
            // Buscar etapa "Primer contacto"
            const primerContactoStage = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primer contacto']],
                ['sequence'],
                { limit: 1 }
            );

            let domain = [];
            
            if (primerContactoStage.length > 0) {
                const sequence = primerContactoStage[0].sequence;
                domain = [
                    ['stage_id.sequence', '>', sequence],      // ✅ Después de primer contacto
                    ['application_status', '!=', 'refused'],  // ✅ NO rechazados
                    ['application_status', '!=', 'hired']     // ✅ NO contratados
                ];
            } else {
                console.error("❌ KpisGrid: Etapa 'Primer contacto' no encontrada en navegación");
                // Sin modal, usar dominio básico
                domain = [["application_status", "=", "ongoing"]];
            }
            
            domain = this._addDateRangeToDomain(domain);

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "🔄 Postulaciones en Progreso (Post-Primer Contacto)",
                res_model: "hr.applicant",
                domain: domain,
                views: [[false, "list"], [false, "form"]],
            });
            
        } catch (error) {
            console.error("❌ KpisGrid: Error en navegación En Progreso:", error);
        }
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

    closeModal() {
        this.state.showModal = false;
    }
}