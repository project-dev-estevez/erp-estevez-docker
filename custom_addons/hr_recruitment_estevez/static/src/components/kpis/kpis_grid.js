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
            openPositions: { value: 0 },
            pendingRequisitions: { value: 0 },
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
                name: "Vacantes Abiertas",
                value: this.state.openPositions.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewOpenPositions()
            },
            {
                name: "Requisiciones por Aprobar",
                value: this.state.pendingRequisitions.value,
                percentage: 0,
                showPercentage: false,
                onClick: () => this.viewPendingRequisitions()
            }
        ];
    }

    // ✅ Método principal para cargar todos los KPIs
    async loadKpisData() {
        this.state.isLoading = true;
        
        try {
            await Promise.all([
                this.calculateTotalApplicants(),
                this.calculateInProgressApplicants(),
                this.calculatePreselectedApplicants(),
                this.calculateRejectedApplicants(),
                this.calculateHiredApplicants(),
                this.calculateOpenPositions(),
                this.calculatePendingRequisitions(),
            ]);
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
    }

    async calculateOpenPositions() {
        try {
            // ✅ PASO 1: Debug - Ver todas las vacantes primero
            const allJobs = await this.orm.searchRead("hr.job", [], ["name", "active", "no_of_recruitment", "no_of_hired_employee"]);
            // ✅ PASO 2: Contar vacantes realmente abiertas
            // Una vacante está abierta si:
            // - Está activa (active = true)
            // - Tiene vacantes por llenar (no_of_recruitment > no_of_hired_employee)
            let domain = [
                ["active", "=", true],                                      // ✅ Vacante activa
                ["no_of_recruitment", ">", 0],                             // ✅ Tiene vacantes que llenar
                // ✅ Opcional: Que aún tenga vacantes disponibles
                // ["no_of_recruitment", ">", "no_of_hired_employee"]
            ];
            
            const count = await this.orm.searchCount("hr.job", domain);
            this.state.openPositions.value = count;
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando Vacantes Abiertas:", error);
            this.state.openPositions.value = 0;
        }
    }

    async calculatePendingRequisitions() {
        try {
            // ✅ Contar requisiciones en estado 'to_approve' (por aprobar)
            let domain = [
                ["state", "=", "to_approve"]  // Estado por aprobar
            ];
            
            // ✅ Si quieres aplicar filtros de fecha, puedes usar:
            // domain = this._addDateRangeToDomain(domain);

            const count = await this.orm.searchCount("hr.requisition", domain);
            this.state.pendingRequisitions.value = count;
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando Requisiciones por Aprobar:", error);
            this.state.pendingRequisitions.value = 0;
        }
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
            context: {
                ...context,
                list_view_ref: "hr_recruitment_estevez.hr_applicant_rejected_list_view",
                search_default_group_by_refuse_reason: 1,  // ✅ Agrupar por motivo de rechazo
                search_default_filter_refused: 1           // ✅ Filtro por rechazados
            }
        });
    }

    viewHiredApplicants() 
    {
        let domain = [["application_status", "=", "hired"]];
        domain = this._getHiredDateRangeDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "✅ Candidatos Contratados",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: {
                // ✅ NUEVO: Configuración de vista personalizada
                list_view_ref: "hr_recruitment_estevez.hr_applicant_hired_list_view",
                search_default_filter_hired: 1,  // ✅ Filtro por contratados
                search_default_group_by_job: 1   // ✅ Agrupar por puesto de trabajo
            }
        });
    }

    viewOpenPositions() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "💼 Vacantes Abiertas",
            res_model: "hr.job",
            domain: [
                ["active", "=", true],              // ✅ Vacantes activas
                ["no_of_recruitment", ">", 0]       // ✅ Con vacantes por llenar
            ],
            views: [[false, "list"], [false, "form"]],
            context: {
                search_default_group_by_department: 1,  // ✅ Agrupar por departamento
                // search_default_filter_open: 1        // ✅ Comentar si causa problemas
            }
        });
    }

    viewPendingRequisitions() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "📋 Requisiciones por Aprobar",
            res_model: "hr.requisition",
            domain: [
                ["state", "=", "to_approve"]
            ],
            views: [[false, "list"], [false, "form"]],
            context: {
                search_default_group_by_requestor: 1,        // ✅ Agrupar por solicitante
                search_default_filter_pending: 1,            // ✅ Filtro por pendientes
                // search_default_group_by_department: 1     // ✅ Alternativa: agrupar por departamento
            }
        });
    }

    closeModal() {
        this.state.showModal = false;
    }
}