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
            totalEmployees: { value: 0, series: [], labels: [], dates: [] }, // ✅ Agregamos dates para los clicks
            activeEmployees: { value: 0 },
            inactiveEmployees: { value: 0 },
            newThisMonth: { value: 0, startDate: null, endDate: null }, // ✅ Agregamos fechas del mes
            upcomingBirthdays: { value: 0, employees: [], startDate: null, endDate: null }, // ✅ Agregamos empleados y fechas
            expiringContracts: { value: 0, contracts: [], startDate: null, endDate: null }, // ✅ Agregamos contratos y fechas
            expiredContracts: { value: 0, contracts: [], startDate: null, endDate: null }, // ✅ NUEVO: Contratos vencidos
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
                onClick: () => this.viewTotalEmployees(),
                onPointClick: (dayIndex, dayName) => this.viewEmployeesByDay(dayIndex, dayName) // ✅ NUEVO: Click en punto específico
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
                name: "Cumpleaños del Mes",
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
            },
            {
                name: "Contratos Vencidos",
                value: this.state.expiredContracts.value,
                secondaryValue: 0,
                showSecondaryValue: false,
                showChart: false,
                onClick: () => this.viewExpiredContracts()
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
                this.calculateExpiredContracts(), // ✅ NUEVO: Contratos vencidos
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
            let dates = []; // ✅ NUEVO: Guardar las fechas para los clicks
            const diasSemana = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
            
            for (let i = 6; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(today.getDate() - i);
                const dateStr = date.toISOString().slice(0, 10);
                
                // Obtener el nombre del día en español
                const dayName = diasSemana[date.getDay()];
                labels.push(dayName);
                dates.push(dateStr); // ✅ NUEVO: Guardar la fecha
                
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
            this.state.totalEmployees.dates = dates; // ✅ NUEVO: Guardar las fechas
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Total Empleados:", error);
            this.state.totalEmployees.value = 0;
            this.state.totalEmployees.series = [];
            this.state.totalEmployees.labels = [];
            this.state.totalEmployees.dates = [];
        }
    }

    async calculateActiveEmployees() {
        try {
            // ✅ TODO: Implementar lógica real
            const count = await this.orm.searchCount("hr.employee", [["active", "=", true]]);
            this.state.activeEmployees.value = count;
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
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Empleados Inactivos:", error);
            this.state.inactiveEmployees.value = 0;
        }
    }

    async calculateNewThisMonth() {
        try {
            // ✅ Obtener el primer y último día del mes actual
            const today = new Date();
            const year = today.getFullYear();
            const month = today.getMonth(); // 0-indexed (Enero = 0)
            
            // Primer día del mes
            const firstDay = new Date(year, month, 1);
            const firstDayStr = firstDay.toISOString().slice(0, 10) + " 00:00:00";
            
            // Último día del mes
            const lastDay = new Date(year, month + 1, 0); // Día 0 del siguiente mes = último día del mes actual
            const lastDayStr = lastDay.toISOString().slice(0, 10) + " 23:59:59";
            
            // ✅ Contar empleados creados este mes
            const domain = [
                ["create_date", ">=", firstDayStr],
                ["create_date", "<=", lastDayStr]
            ];
            
            const count = await this.orm.searchCount(
                "hr.employee", 
                domain,
                { context: { active_test: false } } // Incluir activos e inactivos
            );
            
            this.state.newThisMonth.value = count;
            
            // ✅ Guardar las fechas para la navegación
            this.state.newThisMonth.startDate = firstDayStr;
            this.state.newThisMonth.endDate = lastDayStr;
            
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Nuevos este Mes:", error);
            this.state.newThisMonth.value = 0;
        }
    }

    async calculateUpcomingBirthdays() {
        try {
            // ✅ Obtener el mes actual
            const today = new Date();
            const currentMonth = today.getMonth(); // 0-indexed (Enero = 0)
            
            // ✅ Obtener todos los empleados activos con fecha de nacimiento
            const employees = await this.orm.searchRead(
                "hr.employee",
                [
                    ["active", "=", true],
                    ["birthday", "!=", false] // Que tengan fecha de cumpleaños
                ],
                ["id", "name", "birthday"]
            );

            // ✅ Filtrar empleados que cumplen años en el mes actual
            let birthdaysThisMonth = [];
            
            employees.forEach(employee => {
                if (employee.birthday) {
                    // Leer mes y día directo de 'YYYY-MM-DD': new Date() lo toma como UTC
                    // y en México lo recorre al día anterior (el día 1 caía en el mes previo)
                    const [, month, day] = employee.birthday.split("-").map(Number);
                    const birthdayMonth = month - 1;

                    // Verificar si el cumpleaños es en el mes actual
                    if (birthdayMonth === currentMonth) {
                        birthdaysThisMonth.push({
                            ...employee,
                            birthdayDay: day
                        });
                    }
                }
            });

            // ✅ Ordenar por día del mes
            birthdaysThisMonth.sort((a, b) => a.birthdayDay - b.birthdayDay);

            // ✅ Calcular primer y último día del mes actual para las fechas
            const firstDay = new Date(today.getFullYear(), currentMonth, 1);
            const lastDay = new Date(today.getFullYear(), currentMonth + 1, 0);

            this.state.upcomingBirthdays.value = birthdaysThisMonth.length;
            this.state.upcomingBirthdays.employees = birthdaysThisMonth; // ✅ Guardar empleados para navegación
            this.state.upcomingBirthdays.startDate = firstDay.toISOString().slice(0, 10);
            this.state.upcomingBirthdays.endDate = lastDay.toISOString().slice(0, 10);
            
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Cumpleaños del Mes:", error);
            this.state.upcomingBirthdays.value = 0;
        }
    }

    async calculateExpiringContracts() {
        try {
            // ✅ Obtener fecha actual y fecha límite (próximos 15 días)
            const today = new Date();
            const endDate = new Date(today);
            endDate.setDate(today.getDate() + 15); // Próximos 15 días

            const todayStr = today.toISOString().slice(0, 10);
            const endDateStr = endDate.toISOString().slice(0, 10);
            
            // ✅ Buscar contratos activos que vencen en los próximos 15 días
            const expiringContracts = await this.orm.searchRead(
                "hr.contract",
                [
                    ["state", "=", "open"], // Solo contratos activos
                    ["date_end", "!=", false], // Que tengan fecha de fin
                    ["date_end", ">=", todayStr], // Que no hayan vencido aún
                    ["date_end", "<=", endDateStr] // Que venzan en los próximos 15 días
                ],
                ["id", "name", "employee_id", "date_end", "state"]
            );

            this.state.expiringContracts.value = expiringContracts.length;
            this.state.expiringContracts.contracts = expiringContracts; // ✅ Guardar contratos para navegación
            this.state.expiringContracts.startDate = todayStr;
            this.state.expiringContracts.endDate = endDateStr;

        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Contratos por Vencer:", error);
            this.state.expiringContracts.value = 0;
        }
    }

    async calculateExpiredContracts() {
        try {
            // ✅ Obtener fecha actual
            const today = new Date();
            const todayStr = today.toISOString().slice(0, 10);
            
            // ✅ Buscar TODOS los contratos que vencieron (sin límite de fecha)
            const expiredContracts = await this.orm.searchRead(
                "hr.contract",
                [
                    ["state", "=", "close"], // Solo contratos cerrados
                    ["date_end", "!=", false], // Que tengan fecha de fin
                    ["date_end", "<", todayStr], // Que hayan vencido (fecha de fin < hoy)
                    // ✅ No filtrar por rango de fechas - TODOS los vencidos con state=close
                ],
                ["id", "name", "employee_id", "date_end", "state"]
            );

            this.state.expiredContracts.value = expiredContracts.length;
            this.state.expiredContracts.contracts = expiredContracts; // ✅ Guardar contratos para navegación
            this.state.expiredContracts.startDate = null; // No hay fecha de inicio
            this.state.expiredContracts.endDate = todayStr;
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Contratos Vencidos:", error);
            this.state.expiredContracts.value = 0;
        }
    }

    // ✅ NUEVO: Método para manejar click en punto específico de la gráfica
    async viewEmployeesByDay(dayIndex, dayName) {
        try {
            const selectedDate = this.state.totalEmployees.dates[dayIndex];
            if (!selectedDate) {
                console.error("❌ No se encontró la fecha para el índice:", dayIndex);
                return;
            }

            const domain = [
                ["create_date", ">=", selectedDate + " 00:00:00"],
                ["create_date", "<=", selectedDate + " 23:59:59"]
            ];

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `👥 Empleados creados el ${dayName} (${selectedDate})`,
                res_model: "hr.employee",
                domain: domain,
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                view_mode: "kanban,list,form",
                context: {
                    active_test: false, // ✅ Mostrar activos e inactivos
                    search_default_group_by_department: 1, // ✅ Agrupar por departamento
                },
                clearBreadcrumbs: true
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación por día:", error);
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
                },
                clearBreadcrumbs: true
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
                },
                clearBreadcrumbs: true
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Empleados Inactivos:", error);
        }
    }

    async viewNewThisMonth() {
        try {
            // ✅ Verificar que tenemos las fechas del mes
            if (!this.state.newThisMonth.startDate || !this.state.newThisMonth.endDate) {
                console.error("❌ No se encontraron las fechas del mes actual");
                return;
            }

            // ✅ Obtener nombre del mes actual
            const today = new Date();
            const monthNames = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ];
            const currentMonth = monthNames[today.getMonth()];
            const currentYear = today.getFullYear();

            // ✅ Crear dominio para empleados del mes actual
            const domain = [
                ["create_date", ">=", this.state.newThisMonth.startDate],
                ["create_date", "<=", this.state.newThisMonth.endDate]
            ];

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `🚀 Empleados Nuevos - ${currentMonth} ${currentYear}`,
                res_model: "hr.employee",
                domain: domain,
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                view_mode: "kanban,list,form",
                context: {
                    active_test: false, // ✅ Mostrar activos e inactivos
                    search_default_group_by_department: 1, // ✅ Agrupar por departamento
                    search_default_group_by_create_date: 1, // ✅ También agrupar por fecha de creación
                },
                clearBreadcrumbs: true
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Nuevos este Mes:", error);
        }
    }

    async viewUpcomingBirthdays() {
        try {
            // ✅ Obtener nombre del mes actual
            const today = new Date();
            const monthNames = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ];
            const currentMonth = monthNames[today.getMonth()];

            // ✅ Verificar que tenemos empleados con cumpleaños en el mes
            if (!this.state.upcomingBirthdays.employees || this.state.upcomingBirthdays.employees.length === 0) {
                // ✅ Nadie cumple este mes: mostrar la vista vacía, no a todos los empleados
                const domain = [
                    ["id", "in", []]
                ];

                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: `🎂 Cumpleaños de ${currentMonth}`,
                    res_model: "hr.employee",
                    domain: domain,
                    views: [[false, "kanban"], [false, "list"], [false, "form"]],
                    view_mode: "kanban,list,form",
                    context: {
                        search_default_group_by_department: 1,
                    }
                });
                return;
            }

            // ✅ Obtener IDs de empleados con cumpleaños en el mes
            const employeeIds = this.state.upcomingBirthdays.employees.map(emp => emp.id);

            // ✅ Crear dominio con los IDs específicos
            const domain = [
                ["id", "in", employeeIds]
            ];

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `🎂 Cumpleaños de ${currentMonth} (${this.state.upcomingBirthdays.value} empleados)`,
                res_model: "hr.employee",
                domain: domain,
                views: [[false, "kanban"], [false, "list"], [false, "form"]],
                view_mode: "kanban,list,form",
                context: {
                    search_default_group_by_department: 1,
                    default_view_kanban: 1,
                }
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Cumpleaños del Mes:", error);
        }
    }

    async viewExpiringContracts() {
        try {
            // ✅ Verificar que tenemos contratos por vencer
            if (!this.state.expiringContracts.contracts || this.state.expiringContracts.contracts.length === 0) {
                // ✅ Si no hay contratos específicos, crear filtro general
                const today = new Date();
                const endDate = new Date(today);
                endDate.setDate(today.getDate() + 15); // Próximos 15 días

                const todayStr = today.toISOString().slice(0, 10);
                const endDateStr = endDate.toISOString().slice(0, 10);

                // ✅ Crear dominio general para contratos activos con fecha de fin
                const domain = [
                    ["state", "=", "open"],
                    ["date_end", "!=", false],
                    ["date_end", ">=", todayStr],
                    ["date_end", "<=", endDateStr] // ✅ Límite: próximos 15 días
                ];

                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: "📄 Contratos por Vencer (próximos 15 días)",
                    res_model: "hr.contract",
                    domain: domain,
                    views: [[false, "list"], [false, "form"]],
                    view_mode: "list,form",
                    context: {
                        search_default_group_by_employee: 1, // ✅ Agrupar por empleado
                        search_default_group_by_date_end: 1, // ✅ Agrupar por fecha de fin
                    },
                    clearBreadcrumbs: true
                });
                return;
            }

            // ✅ Obtener IDs de contratos que vencen próximamente
            const contractIds = this.state.expiringContracts.contracts.map(contract => contract.id);

            // ✅ Crear dominio con los IDs específicos
            const domain = [
                ["id", "in", contractIds]
            ];

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `📄 Contratos por Vencer (${this.state.expiringContracts.value} contratos - próximos 15 días)`,
                res_model: "hr.contract",
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                view_mode: "list,form",
                context: {
                    search_default_group_by_date_end: 1, // ✅ Agrupar por fecha de vencimiento
                    search_default_filter_expiring: 1, // ✅ Filtro por vencimiento si existe
                    // ✅ Ordenar por fecha de vencimiento
                    orderby: "date_end asc"
                },
                clearBreadcrumbs: true
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Contratos por Vencer:", error);
        }
    }

    async viewExpiredContracts() {
        try {
            // ✅ Verificar que tenemos contratos vencidos
            if (!this.state.expiredContracts.contracts || this.state.expiredContracts.contracts.length === 0) {
                // ✅ Si no hay contratos específicos, crear filtro general
                const today = new Date();
                const todayStr = today.toISOString().slice(0, 10);

                // ✅ Crear dominio general para contratos vencidos
                const domain = [
                    ["state", "=", "close"],
                    ["date_end", "!=", false],
                    ["date_end", "<", todayStr]
                ];

                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: "❌ Contratos Vencidos (Todos)",
                    res_model: "hr.contract",
                    domain: domain,
                    views: [[false, "list"], [false, "form"]],
                    view_mode: "list,form",
                    context: {
                        search_default_group_by_employee: 1, // ✅ Agrupar por empleado
                        search_default_group_by_state: 1, // ✅ Agrupar por estado
                        orderby: "date_end desc" // ✅ Ordenar por fecha de vencimiento descendente
                    }
                });
                return;
            }

            // ✅ Obtener IDs de contratos vencidos
            const contractIds = this.state.expiredContracts.contracts.map(contract => contract.id);

            // ✅ Crear dominio con los IDs específicos
            const domain = [
                ["id", "in", contractIds]
            ];

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `❌ Contratos Vencidos (${this.state.expiredContracts.value} contratos)`,
                res_model: "hr.contract",
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                view_mode: "list,form",
                context: {
                    // search_default_group_by_state: 1, // ✅ Agrupar por estado del contrato
                    // search_default_filter_expired: 1, // ✅ Filtro por vencidos si existe
                    // ✅ Ordenar por fecha de vencimiento descendente (más recientes primero)
                    orderby: "date_end desc"
                }
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Contratos Vencidos:", error);
        }
    }
}
