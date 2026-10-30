/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
// Misma tarjeta que el dashboard de Empleados, para que ambos se vean iguales
import { KpiCard } from "@hr_estevez/components/kpis/kpi_card/kpi_card";
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
        this.recruitmentStageService = useService("recruitment_stage");
        
        // ✅ Estado local para los KPIs
        this.state = useState({
            totalApplicants: { value: 0 },
            inProgressApplicants: { value: 0 },
            rejectedApplicants: { value: 0 },
            hiredApplicants: { value: 0, secondaryValue: 0 },
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

    _getCombinedHiredDomain() {
        if (!this.props.startDate || !this.props.endDate) {
            // Si no hay fechas, mostrar todos los contratados
            return [['application_status', '=', 'hired']];
        }

        return [
            '|', // ✅ Operador OR de Odoo
            // Grupo 1: Creados Y contratados en el rango
            '&',
            ['application_status', '=', 'hired'],
            '&',
            ['create_date', '>=', this.props.startDate],
            ['create_date', '<=', this.props.endDate],
            // Grupo 2: Contratados en el rango PERO creados antes
            '&',
            ['application_status', '=', 'hired'],
            '&',
            ['date_closed', '>=', this.props.startDate],
            '&',
            ['date_closed', '<=', this.props.endDate],
            ['create_date', '<', this.props.startDate]
        ];
    }

    get kpis() {
        const hired = this.state.hiredApplicants;
        return [
            {
                name: "Postulaciones",
                value: this.state.totalApplicants.value,
                icon: "fa-inbox",
                color: "primary",
                subtitle: "Desde primer contacto",
                tooltip: "Postulaciones del periodo que llegaron al menos a primer contacto",
                onClick: () => this.viewTotalApplicants()
            },
            {
                name: "En Proceso",
                value: this.state.inProgressApplicants.value,
                icon: "fa-spinner",
                color: "info",
                subtitle: "Sin decisión aún",
                tooltip: "Postulaciones del periodo que siguen activas: ni rechazadas ni contratadas",
                onClick: () => this.viewInProgressApplicants()
            },
            {
                name: "Contratados",
                // Incluye a quienes se postularon antes del periodo y se contrataron en él
                value: hired.value + hired.secondaryValue,
                icon: "fa-handshake-o",
                color: "success",
                subtitle: hired.secondaryValue ? `${hired.secondaryValue} de postulaciones anteriores` : "En el periodo",
                tooltip: "Candidatos contratados en el periodo",
                onClick: () => this.viewHiredApplicants()
            },
            {
                name: "Rechazados",
                value: this.state.rejectedApplicants.value,
                icon: "fa-user-times",
                color: "danger",
                subtitle: "Incluye declinaciones",
                tooltip: "Postulaciones del periodo rechazadas o declinadas después de primer contacto",
                onClick: () => this.viewRejectedApplicants()
            },
            {
                name: "Vacantes Abiertas",
                value: this.state.openPositions.value,
                icon: "fa-briefcase",
                color: "warning",
                subtitle: "Publicadas hoy",
                tooltip: "Requisiciones aprobadas y publicadas",
                onClick: () => this.viewOpenPositions()
            },
            {
                name: "Requisiciones por Aprobar",
                value: this.state.pendingRequisitions.value,
                icon: "fa-clipboard",
                color: "secondary",
                subtitle: "Esperando aprobación",
                tooltip: "Requisiciones de personal pendientes de aprobación",
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
            // ✅ NUEVO: Usar el servicio en lugar de consulta directa
            const firstContactStage = await this.recruitmentStageService.getFirstContactStage();
            
            if (!firstContactStage) {
                this.state.totalApplicants.value = 0;
                return;
            }

            // ✅ Contar candidatos que han llegado al menos a "Primer contacto"
            let domain = [
                ['stage_id.sequence', '>=', firstContactStage.sequence]
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
            const firstContactStage = await this.recruitmentStageService.getFirstContactStage();
            
            if (!firstContactStage) {
                console.error("❌ KpisGrid: Etapa 'Primer contacto' NO encontrada para En Progreso");
                this.state.inProgressApplicants.value = 0;
                return;
            }

            // ✅ Contar candidatos que han superado "Primer contacto" 
            //    PERO que NO están rechazados ni contratados
            let domain = [
                ['stage_id.sequence', '>=', firstContactStage.sequence],    // ✅ Después de primer contacto
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

    async calculateRejectedApplicants() {
        try {
            const rejectedDomain = await this.recruitmentStageService.getRejectedDomainFromFirstContact(
                this._addDateRangeToDomain([])
            );

            const count = await this.orm.searchCount(
                "hr.applicant", 
                rejectedDomain, 
                { context: { active_test: false } }
            );

            this.state.rejectedApplicants.value = count;
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando Rechazados:", error);
            this.state.rejectedApplicants.value = 0;
        }
    }

    async calculateHiredApplicants() {
        try {
            // ✅ KPI PRINCIPAL: Creados en el rango Y contratados
            let primaryDomain = [["application_status", "=", "hired"]];
            primaryDomain = this._addDateRangeToDomain(primaryDomain);

            const primaryCount = await this.orm.searchCount("hr.applicant", primaryDomain);
            this.state.hiredApplicants.value = primaryCount;

            // ✅ KPI SECUNDARIO: Contratados en el rango PERO creados antes
            const secondaryCount = await this.calculateHiredInRangeButCreatedBefore();
            this.state.hiredApplicants.secondaryValue = secondaryCount;

            console.log(`📊 KPI Contratados - Principal: ${primaryCount}, Secundario: ${secondaryCount}`);

        } catch (error) {
            console.error("❌ KpisGrid: Error calculando Contratados:", error);
            this.state.hiredApplicants.value = 0;
            this.state.hiredApplicants.secondaryValue = 0;
        }
    }

    async calculateHiredInRangeButCreatedBefore() {
        try {
            if (!this.props.startDate || !this.props.endDate) {
                return 0;
            }

            // Dominio: contratados en el rango de fechas PERO creados ANTES del rango
            let domain = [
                ["application_status", "=", "hired"],
                ["date_closed", ">=", this.props.startDate],     // ✅ Contratado en el rango
                ["date_closed", "<=", this.props.endDate],       // ✅ Contratado en el rango
                ["create_date", "<", this.props.startDate]       // ✅ Creado ANTES del rango
            ];

            const count = await this.orm.searchCount("hr.applicant", domain);
            return count;
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando contratados secundario:", error);
            return 0;
        }
    }

    async calculateOpenPositions() {
        try {
            let domain = [
                ["is_published", "=", true],
            ];
            
            const count = await this.orm.searchCount("hr.requisition", domain);            
            this.state.openPositions.value = count;
            
        } catch (error) {
            console.error("❌ KpisGrid: Error calculando Vacantes Abiertas:", error);
            this.state.openPositions.value = 0;
        }
    }

    async calculatePendingRequisitions() {
        try {
            // Requisiciones esperando aprobación (Dirección o final)
            let domain = [
                ["state", "in", ["to_approve", "first_approval"]]
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
            const firstContactStage = await this.recruitmentStageService.getFirstContactStage();

            let domain = [];
            
            if (firstContactStage) {
                domain = [
                    ['stage_id.sequence', '>=', firstContactStage.sequence],      // ✅ Después de primer contacto
                    ['application_status', '!=', 'refused'],  // ✅ NO rechazados
                    ['application_status', '!=', 'hired']     // ✅ NO contratados
                ];
            } else {
                console.error("❌ KpisGrid: Etapa 'Primer contacto' no encontrada en navegación");
                // Fallback: usar dominio básico
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

    async viewRejectedApplicants() {
        try {
            // ✅ NUEVO: Usar el servicio para obtener dominio de rechazados desde primer contacto
            const rejectedDomain = await this.recruitmentStageService.getRejectedDomainFromFirstContact(
                this._addDateRangeToDomain([])
            );

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "❌ Postulaciones Rechazadas (Post-Primer Contacto)",
                res_model: "hr.applicant",
                domain: rejectedDomain,
                views: [[false, "list"], [false, "form"]],
                context: {
                    active_test: false,
                    list_view_ref: "hr_recruitment_estevez.hr_applicant_rejected_list_view",
                    search_default_group_by_refuse_reason: 1,  // ✅ Agrupar por motivo de rechazo
                    search_default_filter_refused: 1           // ✅ Filtro por rechazados
                }
            });
        } catch (error) {
            console.error("❌ KpisGrid: Error en navegación Rechazados:", error);
        }
    }

    viewHiredApplicants() 
    {
        const domain = this._getCombinedHiredDomain();

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

        let domain = [
            ["is_published", "=", true],
        ];

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "💼 Vacantes Abiertas",
            res_model: "hr.requisition",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: {
                search_default_filter_open_positions: 1,
            }
        });
    }

    viewPendingRequisitions() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "📋 Requisiciones por Aprobar",
            res_model: "hr.requisition",
            domain: [
                ["state", "in", ["to_approve", "first_approval"]]
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