/** @odoo-module */

export const chartsDummy = [
    {
        title: "Distribución por Departamento",
        type: "bar",
        config: {
            categories: ["Ventas", "Producción", "RRHH", "Finanzas", "IT"],
            series: [{
                name: "Empleados",
                data: [12, 18, 7, 9, 5]
            }],
        },
    },
    {
        title: "Empleados por Estado",
        type: "pie",
        config: {
            labels: ["Activos", "Inactivos", "Vacaciones"],
            series: [98, 22, 5],
        },
    },
    {
        title: "Contratos por Vencer (Meses)",
        type: "line",
        config: {
            categories: ["Ago", "Sep", "Oct", "Nov", "Dic"],
            series: [{
                name: "Contratos",
                data: [2, 3, 1, 0, 1]
            }],
        },
    },
    {
        title: "Cumpleaños Próximos",
        type: "donut",
        config: {
            labels: ["Semana 1", "Semana 2", "Semana 3", "Semana 4"],
            series: [1, 0, 2, 0],
        },
    },
];
