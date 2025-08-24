/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { KpiCard } from "./kpi_card/kpi_card";
import { KpiChartCard } from "./kpi_chart_card/kpi_chart_card";

export class KpisGrid extends Component {

    static template = "hr_estevez.KpisGrid";
    static components = { KpiCard, KpiChartCard };
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
            totalEmployees: { value: 0, series: [], labels: [] }, // ✅ Incluye series y labels para la gráfica
            activeEmployees: { value: 0 },
            inactiveEmployees: { value: 0 },
            newThisMonth: { value: 0 },
            upcomingBirthdays: { value: 0 },
            expiringContracts: { value: 0 },
            isLoading: true,
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

    // ✅ Métodos de filtrado por fechas (para futuros KPIs que lo necesiten)
    _addDateRangeToDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["create_date", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["create_date", "<=", this.props.endDate]);
        }
        return domain;
    }

    get kpis() {
        return [
            {
                name: "Total Empleados",
                value: this.state.totalEmployees.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: true, // ✅ Solo este KPI tendrá gráfica
                series: this.state.totalEmployees.series,
                labels: this.state.totalEmployees.labels, // ✅ NUEVO: Pasar las etiquetas
                onClick: () => this.viewTotalEmployees()
            },
            {
                name: "Empleados Activos",
                value: this.state.activeEmployees.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: false,
                onClick: () => this.viewActiveEmployees()
            },
            {
                name: "Empleados Inactivos",
                value: this.state.inactiveEmployees.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: false,
                onClick: () => this.viewInactiveEmployees()
            },
            {
                name: "Nuevos este Mes",
                value: this.state.newThisMonth.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: false,
                onClick: () => this.viewNewThisMonth()
            },
            {
                name: "Cumpleaños Próximos",
                value: this.state.upcomingBirthdays.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: false,
                onClick: () => this.viewUpcomingBirthdays()
            },
            {
                name: "Contratos por Vencer",
                value: this.state.expiringContracts.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: false,
                onClick: () => this.viewExpiringContracts()
            }
        ];
    }

    // ✅ Método principal para cargar todos los KPIs
    async loadKpisData() {
        this.state.isLoading = true;
        
        try {
            await Promise.all([
                this.calculateTotalEmployees(),
                this.calculateActiveEmployees(),
                this.calculateInactiveEmployees(),
                this.calculateNewThisMonth(),
                this.calculateUpcomingBirthdays(),
                this.calculateExpiringContracts(),
            ]);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error cargando datos:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async calculateTotalEmployees() {
        try {
            // ✅ Contar TODOS los empleados (activos e inactivos)
            const count = await this.orm.searchCount(
                "hr.employee", 
                [], // Sin filtros - todos los empleados
                { context: { active_test: false } } // Incluir inactivos
            );

            this.state.totalEmployees.value = count;

            // ✅ NUEVO: Calcular series para la gráfica (últimos 7 días)
            const today = new Date();
            let series = [];
            let labels = [];
            const diasSemana = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
            
            for (let i = 6; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(today.getDate() - i);
                const dateStr = date.toISOString().slice(0, 10);
                
                // Obtener el nombre del día en español
                const dayName = diasSemana[date.getDay()];
                labels.push(dayName);
                
                const dayCount = await this.orm.searchCount(
                    "hr.employee", 
                    [
                        ["create_date", ">=", dateStr + " 00:00:00"], 
                        ["create_date", "<=", dateStr + " 23:59:59"]
                    ],
                    { context: { active_test: false } }
                );
                series.push(dayCount);
            }

            this.state.totalEmployees.series = series;
            this.state.totalEmployees.labels = labels; // ✅ NUEVO: Guardar las etiquetas
            console.log(`📊 KPI Total Empleados: ${count}, Series: [${series.join(', ')}], Labels: [${labels.join(', ')}]`);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Total Empleados:", error);
            this.state.totalEmployees.value = 0;
            this.state.totalEmployees.series = [];
            this.state.totalEmployees.labels = [];
        }
    }

    async calculateActiveEmployees() {
        try {
            // ✅ TODO: Implementar lógica real
            const count = await this.orm.searchCount("hr.employee", [["active", "=", true]]);
            this.state.activeEmployees.value = count;
            console.log(`📊 KPI Empleados Activos: ${count}`);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Empleados Activos:", error);
            this.state.activeEmployees.value = 0;
        }
    }

    async calculateInactiveEmployees() {
        try {
            // ✅ TODO: Implementar lógica real
            const count = await this.orm.searchCount(
                "hr.employee", 
                [["active", "=", false]], 
                { context: { active_test: false } }
            );
            this.state.inactiveEmployees.value = count;
            console.log(`📊 KPI Empleados Inactivos: ${count}`);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Empleados Inactivos:", error);
            this.state.inactiveEmployees.value = 0;
        }
    }

    async calculateNewThisMonth() {
        try {
            // ✅ TODO: Implementar lógica para empleados nuevos este mes
            this.state.newThisMonth.value = 0; // Temporal
            console.log(`📊 KPI Nuevos este Mes: 0 (temporal)`);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Nuevos este Mes:", error);
            this.state.newThisMonth.value = 0;
        }
    }

    async calculateUpcomingBirthdays() {
        try {
            // ✅ TODO: Implementar lógica para cumpleaños próximos
            this.state.upcomingBirthdays.value = 0; // Temporal
            console.log(`📊 KPI Cumpleaños Próximos: 0 (temporal)`);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Cumpleaños Próximos:", error);
            this.state.upcomingBirthdays.value = 0;
        }
    }

    async calculateExpiringContracts() {
        try {
            // ✅ TODO: Implementar lógica para contratos por vencer
            this.state.expiringContracts.value = 0; // Temporal
            console.log(`📊 KPI Contratos por Vencer: 0 (temporal)`);
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Contratos por Vencer:", error);
            this.state.expiringContracts.value = 0;
        }
    }

    // ✅ Métodos de navegación
    async viewTotalEmployees() {
        try {
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "👥 Total de Empleados",
                res_model: "hr.employee",
                domain: [], // Sin filtros - mostrar todos
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                view_mode: "kanban,list,form",
                context: {
                    active_test: false, // ✅ Mostrar activos e inactivos
                    search_default_group_by_department: 1, // ✅ Agrupar por departamento
                }
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Total Empleados:", error);
        }
    }

    async viewActiveEmployees() {
        try {
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "✅ Empleados Activos",
                res_model: "hr.employee",
                domain: [["active", "=", true]],
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                view_mode: "kanban,list,form",
                context: {
                    search_default_group_by_department: 1,
                }
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Empleados Activos:", error);
        }
    }

    async viewInactiveEmployees() {
        try {
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "❌ Empleados Inactivos",
                res_model: "hr.employee",
                domain: [["active", "=", false]],
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                view_mode: "kanban,list,form",
                context: {
                    active_test: false,
                    search_default_group_by_department: 1,
                }
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Empleados Inactivos:", error);
        }
    }

    async viewNewThisMonth() {
        try {
            // ✅ TODO: Implementar navegación para nuevos este mes
            console.log("🚀 Navegando a Nuevos este Mes (pendiente implementar)");
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Nuevos este Mes:", error);
        }
    }

    async viewUpcomingBirthdays() {
        try {
            // ✅ TODO: Implementar navegación para cumpleaños próximos
            console.log("🎂 Navegando a Cumpleaños Próximos (pendiente implementar)");
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Cumpleaños Próximos:", error);
        }
    }

    async viewExpiringContracts() {
        try {
            // ✅ TODO: Implementar navegación para contratos por vencer
            console.log("📄 Navegando a Contratos por Vencer (pendiente implementar)");
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Contratos por Vencer:", error);
        }
    }
}
