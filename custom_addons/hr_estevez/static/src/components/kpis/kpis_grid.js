/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { serializeDateTime } from "@web/core/l10n/dates";
import { KpiCard } from "./kpi_card/kpi_card";
import { KpiChartCard } from "./kpi_chart_card/kpi_chart_card";

const { DateTime } = luxon;

const MONTH_NAMES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

// Límites del mes actual en la zona horaria del usuario, serializados en UTC
// como los guarda Odoo (create_date, hr.employee.history.date)
function currentMonthRange() {
    const start = DateTime.local().startOf("month");
    return {
        start: serializeDateTime(start),
        end: serializeDateTime(start.endOf("month")),
        label: `${MONTH_NAMES[start.month - 1]} ${start.year}`,
    };
}

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
            newThisMonth: { value: 0, startDate: null, endDate: null }, // ✅ Agregamos fechas del mes
            terminationsThisMonth: { value: 0, employeeIds: [] },
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
        const month = currentMonthRange().label;
        return [
            {
                name: "Total Empleados",
                value: this.state.totalEmployees.value,
                icon: "fa-users",
                color: "primary",
                subtitle: "Altas últimos 7 días",
                tooltip: "Todos los empleados registrados (activos e inactivos)",
                showChart: true, // ✅ Solo este KPI tendrá gráfica
                series: this.state.totalEmployees.series,
                labels: this.state.totalEmployees.labels, // ✅ NUEVO: Pasar las etiquetas
                onClick: () => this.viewTotalEmployees(),
                onPointClick: (dayIndex, dayName) => this.viewEmployeesByDay(dayIndex, dayName) // ✅ NUEVO: Click en punto específico
            },
            {
                name: "Nuevos este Mes",
                value: this.state.newThisMonth.value,
                icon: "fa-user-plus",
                color: "success",
                subtitle: month,
                tooltip: "Empleados dados de alta en el mes actual",
                onClick: () => this.viewNewThisMonth()
            },
            {
                name: "Bajas este Mes",
                value: this.state.terminationsThisMonth.value,
                icon: "fa-user-times",
                color: "danger",
                subtitle: month,
                tooltip: "Empleados dados de baja en el mes actual, según la fecha de baja",
                onClick: () => this.viewTerminationsThisMonth()
            },
            {
                name: "Cumpleaños del Mes",
                value: this.state.upcomingBirthdays.value,
                icon: "fa-birthday-cake",
                color: "info",
                subtitle: MONTH_NAMES[new Date().getMonth()],
                tooltip: "Empleados activos que cumplen años este mes",
                onClick: () => this.viewUpcomingBirthdays()
            },
            {
                name: "Contratos por Vencer",
                value: this.state.expiringContracts.value,
                icon: "fa-hourglass-half",
                color: "warning",
                subtitle: "Próximos 15 días",
                tooltip: "Contratos en curso de empleados activos cuya fecha de fin cae en los próximos 15 días",
                onClick: () => this.viewExpiringContracts()
            },
            {
                name: "Contratos Vencidos",
                value: this.state.expiredContracts.value,
                icon: "fa-calendar-times-o",
                color: "secondary",
                subtitle: "Sin renovar",
                tooltip: "Empleados activos cuyo último contrato ya venció y no tienen otro vigente",
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
                this.calculateNewThisMonth(),
                this.calculateTerminationsThisMonth(),
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

            // ✅ NUEVO: Calcular series para la gráfica (últimos 7 días, en hora local)
            let series = [];
            let labels = [];
            let dates = []; // ✅ NUEVO: Guardar los rangos de cada día para los clicks
            const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

            for (let i = 6; i >= 0; i--) {
                const day = DateTime.local().minus({ days: i }).startOf("day");
                const range = {
                    label: day.toISODate(),
                    start: serializeDateTime(day),
                    end: serializeDateTime(day.endOf("day")),
                };
                labels.push(diasSemana[day.weekday - 1]);
                dates.push(range);

                const dayCount = await this.orm.searchCount(
                    "hr.employee",
                    [
                        ["create_date", ">=", range.start],
                        ["create_date", "<=", range.end]
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

    async calculateNewThisMonth() {
        try {
            // ✅ Primer y último instante del mes actual (hora local, en UTC)
            const { start: firstDayStr, end: lastDayStr } = currentMonthRange();

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

    async calculateTerminationsThisMonth() {
        try {
            // ✅ Las bajas quedan en el historial con la fecha capturada en el asistente de baja
            const { start, end } = currentMonthRange();
            const groups = await this.orm.readGroup(
                "hr.employee.history",
                [
                    ["status", "=", "baja"],
                    ["date", ">=", start],
                    ["date", "<=", end],
                ],
                ["employee_id"],
                ["employee_id"]
            );
            // ✅ Un empleado cuenta una sola vez aunque tenga dos bajas en el mes
            const employeeIds = groups.filter(g => g.employee_id).map(g => g.employee_id[0]);
            this.state.terminationsThisMonth.value = employeeIds.length;
            this.state.terminationsThisMonth.employeeIds = employeeIds;
        } catch (error) {
            console.error("❌ KpisGrid HR: Error calculando Bajas este Mes:", error);
            this.state.terminationsThisMonth.value = 0;
            this.state.terminationsThisMonth.employeeIds = [];
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
            const todayStr = DateTime.local().toISODate();
            const endDateStr = DateTime.local().plus({ days: 15 }).toISODate(); // Próximos 15 días

            // ✅ Buscar contratos activos que vencen en los próximos 15 días
            const expiringContracts = await this.orm.searchRead(
                "hr.contract",
                [
                    ["state", "=", "open"], // Solo contratos activos
                    ["employee_id.active", "=", true], // Solo empleados activos (no bajas)
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
            const todayStr = DateTime.local().toISODate();

            // ✅ Contratos ya vencidos (expirados o aún "en curso" con fecha pasada) de empleados activos
            const ended = await this.orm.searchRead(
                "hr.contract",
                [
                    ["state", "in", ["open", "close"]],
                    ["employee_id.active", "=", true], // Las bajas no cuentan
                    ["date_end", "!=", false],
                    ["date_end", "<", todayStr],
                ],
                ["id", "name", "employee_id", "date_end", "state"],
                { order: "date_end desc" }
            );

            // ✅ Quien ya renovó (tiene un contrato vigente) no cuenta
            const running = await this.orm.searchRead(
                "hr.contract",
                [
                    ["state", "=", "open"],
                    ["employee_id.active", "=", true],
                    "|", ["date_end", "=", false], ["date_end", ">=", todayStr],
                ],
                ["employee_id"]
            );
            const renewed = new Set(running.map((c) => c.employee_id[0]));

            // ✅ Un contrato por empleado: el último que venció
            const seen = new Set();
            const expiredContracts = ended.filter((c) => {
                const employeeId = c.employee_id[0];
                if (renewed.has(employeeId) || seen.has(employeeId)) {
                    return false;
                }
                seen.add(employeeId);
                return true;
            });

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
                ["create_date", ">=", selectedDate.start],
                ["create_date", "<=", selectedDate.end]
            ];

            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `👥 Empleados creados el ${dayName} (${selectedDate.label})`,
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

    async viewTerminationsThisMonth() {
        try {
            const { label } = currentMonthRange();
            const count = this.state.terminationsThisMonth.value;
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `Bajas - ${label} (${count} ${count === 1 ? "empleado" : "empleados"})`,
                res_model: "hr.employee",
                domain: [["id", "in", this.state.terminationsThisMonth.employeeIds]],
                views: [[false, "list"], [false, "kanban"], [false, "form"]],
                view_mode: "list,kanban,form",
                context: {
                    active_test: false, // ✅ Las bajas están archivadas
                    search_default_group_by_department: 1,
                },
            });
        } catch (error) {
            console.error("❌ KpisGrid HR: Error en navegación Bajas este Mes:", error);
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
                const todayStr = DateTime.local().toISODate();
                const endDateStr = DateTime.local().plus({ days: 15 }).toISODate();

                // ✅ Crear dominio general para contratos activos con fecha de fin
                const domain = [
                    ["state", "=", "open"],
                    ["employee_id.active", "=", true],
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
                // ✅ Nadie pendiente de renovar: mostrar la lista vacía, no todos los contratos cerrados
                const domain = [["id", "in", []]];

                await this.actionService.doAction({
                    type: "ir.actions.act_window",
                    name: "❌ Contratos vencidos sin renovar",
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
                name: `❌ Contratos vencidos sin renovar (${this.state.expiredContracts.value})`,
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
