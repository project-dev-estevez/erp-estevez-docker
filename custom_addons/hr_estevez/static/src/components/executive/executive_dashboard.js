/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { escape } from "@web/core/utils/strings";
import { ExecChart, CHART_INK } from "./exec_chart";

// Paleta validada con la guía de visualización (categórica y rampa ordinal)
const COLORS = {
    hires: "#2a78d6",
    exits: "#e34948",
    headcount: "#2a78d6",
    departments: "#2a78d6",
    groups: {
        voluntaria: "#2a78d6",
        involuntaria: "#eb6834",
        fin_contrato: "#1baf7a",
        sin_especificar: "#898781",
    },
    tenure: ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"],
};

const GROUP_LEGEND = [
    { key: "voluntaria", label: "Voluntaria" },
    { key: "involuntaria", label: "Involuntaria" },
    { key: "fin_contrato", label: "Fin de contrato" },
    { key: "sin_especificar", label: "Sin especificar" },
];

const SEVERITY_ICON = {
    critical: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
};

function tooltipBox(title, rows) {
    const body = rows.map(([color, label, value]) => `
        <div class="o_exec_tt_row">
            ${color ? `<span class="o_exec_tt_key" style="background:${color}"></span>` : ""}
            <strong>${escape(String(value))}</strong><span>${escape(label)}</span>
        </div>`).join("");
    return `<div class="o_exec_tt"><div class="o_exec_tt_title">${escape(title)}</div>${body}</div>`;
}

// En celular los nombres de categoría se acortan para dejar espacio a las barras;
// el nombre completo queda en el tooltip y en la vista de tabla
function narrowCategoryLabels(max) {
    return [{
        breakpoint: 576,
        options: {
            yaxis: { max, labels: { maxWidth: 110, style: { colors: CHART_INK.secondary, fontSize: "12px" } } },
            dataLabels: { style: { fontSize: "11px" } },
        },
    }];
}

const AXIS = {
    axisBorder: { show: true, color: CHART_INK.axis },
    axisTicks: { show: false },
    labels: { style: { colors: CHART_INK.muted, fontSize: "12px" } },
};

export class ExecutiveDashboard extends Component {
    static template = "hr_estevez.ExecutiveDashboard";
    static components = { ExecChart };
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.charts = {};
        this.colors = COLORS;
        this.state = useState({
            filters: { months: 12, companyId: false, directionId: false },
            options: { companies: [], directions: [], periods: [3, 6, 12, 24] },
            data: null,
            loading: true,
            tables: {},
        });
        onWillStart(async () => {
            this.state.options = await this.orm.call("hr.executive.dashboard", "get_filter_options", []);
            await this.load();
        });
    }

    async load() {
        this.state.loading = true;
        const { months, companyId, directionId } = this.state.filters;
        const data = await this.orm.call("hr.executive.dashboard", "get_dashboard_data", [], {
            months, company_id: companyId, direction_id: directionId,
        });
        this.charts = this.buildCharts(data);
        this.state.data = data;
        this.state.loading = false;
    }

    // ---------- Filtros ----------
    onFilterChange(key, ev) {
        const value = ev.target.value;
        this.state.filters[key] = key === "months" ? parseInt(value) : (value ? parseInt(value) : false);
        this.load();
    }

    toggleTable(key) {
        this.state.tables[key] = !this.state.tables[key];
    }

    // ---------- Formato ----------
    get periodLabel() {
        const m = this.state.filters.months;
        return m === 12 ? "últimos 12 meses" : `últimos ${m} meses`;
    }

    formatDelta(value, suffix = "") {
        if (!value) {
            return `sin cambio${suffix ? "" : ""}`;
        }
        return `${value > 0 ? "+" : "−"}${Math.abs(value).toLocaleString("es-MX")}${suffix}`;
    }

    get turnoverTrend() {
        const delta = this.state.data.kpis.turnover_delta;
        if (!delta) {
            return { icon: "fa-minus", cls: "text-muted", label: "igual que el periodo anterior" };
        }
        // Más rotación es peor: subir es alerta, bajar es mejora
        return delta > 0
            ? { icon: "fa-arrow-up", cls: "o_exec_delta_bad", label: `${this.formatDelta(delta, " pp")} vs periodo anterior` }
            : { icon: "fa-arrow-down", cls: "o_exec_delta_good", label: `${this.formatDelta(delta, " pp")} vs periodo anterior` };
    }

    get headcountTrend() {
        const delta = this.state.data.kpis.headcount_delta;
        const icon = delta > 0 ? "fa-arrow-up" : delta < 0 ? "fa-arrow-down" : "fa-minus";
        return { icon, label: `${this.formatDelta(delta)} desde el inicio del periodo` };
    }

    get reasonGroups() {
        const present = new Set(this.state.data.reasons.map((r) => r.group));
        return GROUP_LEGEND.filter((g) => present.has(g.key)).map((g) => ({ ...g, color: COLORS.groups[g.key] }));
    }

    get voluntaryShare() {
        const reasons = this.state.data.reasons;
        const total = reasons.reduce((s, r) => s + r.count, 0);
        const voluntary = reasons.filter((r) => r.group === "voluntaria").reduce((s, r) => s + r.count, 0);
        return total ? Math.round((voluntary / total) * 100) : 0;
    }

    severityIcon(severity) {
        return SEVERITY_ICON[severity] || SEVERITY_ICON.info;
    }

    tenureColor(index) {
        return COLORS.tenure[index];
    }

    // ---------- Navegación ----------
    openEmployees(ids, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "hr.employee",
            domain: [["id", "in", ids]],
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            context: { active_test: false },
        });
    }

    openAlert(alert) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `${alert.count} ${alert.label}`,
            res_model: alert.res_model,
            domain: alert.domain,
            views: [[false, "list"], [false, "form"]],
            context: { active_test: false },
        });
    }

    // ---------- Gráficas ----------
    buildCharts(data) {
        const monthly = data.monthly;
        const labels = monthly.map((m) => m.label);

        const headcount = {
            chart: { type: "line", sparkline: { enabled: false } },
            series: [{ name: "Plantilla", data: monthly.map((m) => m.headcount) }],
            colors: [COLORS.headcount],
            stroke: { width: 2, curve: "smooth", lineCap: "round" },
            markers: { size: 0, hover: { size: 5 }, strokeColors: "#fff", strokeWidth: 2 },
            xaxis: { ...AXIS, categories: labels, labels: { show: false }, tooltip: { enabled: false } },
            yaxis: { labels: { style: { colors: CHART_INK.muted }, formatter: (v) => Math.round(v) }, tickAmount: 3, forceNiceScale: true },
            dataLabels: { enabled: false },
            legend: { show: false },
            tooltip: {
                custom: ({ dataPointIndex }) => {
                    const m = monthly[dataPointIndex];
                    return tooltipBox(m.label, [[COLORS.headcount, "empleados al cierre", m.headcount]]);
                },
            },
        };

        const movement = {
            chart: {
                type: "bar",
                stacked: true,
                events: {
                    dataPointSelection: (_e, _c, { seriesIndex, dataPointIndex }) => {
                        const m = monthly[dataPointIndex];
                        if (seriesIndex === 0 && m.hires) {
                            this.openEmployees(m.hire_ids, `Altas · ${m.label}`);
                        } else if (seriesIndex === 1 && m.exits) {
                            this.openEmployees(m.exit_ids, `Bajas · ${m.label}`);
                        }
                    },
                },
            },
            series: [
                { name: "Altas", data: monthly.map((m) => m.hires) },
                { name: "Bajas", data: monthly.map((m) => -m.exits) },
            ],
            colors: [COLORS.hires, COLORS.exits],
            plotOptions: { bar: { columnWidth: "22px", borderRadius: 4, borderRadiusApplication: "end", borderRadiusWhenStacked: "all" } },
            stroke: { show: true, width: 2, colors: ["#fff"] },
            xaxis: { ...AXIS, categories: labels },
            yaxis: { labels: { style: { colors: CHART_INK.muted }, formatter: (v) => Math.abs(Math.round(v)) }, tickAmount: 4, forceNiceScale: true },
            dataLabels: { enabled: false },
            // Leyenda en HTML (plantilla), igual que la de "¿Por qué se van?"
            legend: { show: false },
            states: { hover: { filter: { type: "darken", value: 0.9 } } },
            tooltip: {
                shared: true,
                intersect: false,
                custom: ({ dataPointIndex }) => {
                    const m = monthly[dataPointIndex];
                    return tooltipBox(m.label, [
                        [COLORS.hires, "altas", m.hires],
                        [COLORS.exits, "bajas", m.exits],
                        [null, "rotación del mes", `${m.rate}%`],
                        [null, "plantilla al cierre", m.headcount],
                    ]);
                },
            },
        };

        const reasons = data.reasons;
        const reasonsChart = {
            chart: {
                type: "bar",
                events: {
                    dataPointSelection: (_e, _c, { dataPointIndex }) => {
                        const r = reasons[dataPointIndex];
                        this.openEmployees(r.employee_ids, `Bajas · ${r.label}`);
                    },
                },
            },
            series: [{ name: "Bajas", data: reasons.map((r) => r.count) }],
            colors: reasons.map((r) => COLORS.groups[r.group]),
            plotOptions: { bar: { horizontal: true, distributed: true, barHeight: "22px", borderRadius: 4, borderRadiusApplication: "end", dataLabels: { position: "top" } } },
            xaxis: { ...AXIS, categories: reasons.map((r) => r.label), labels: { show: false } },
            yaxis: { max: Math.max(...reasons.map((r) => r.count), 1) * 1.2, labels: { style: { colors: CHART_INK.secondary, fontSize: "13px" }, maxWidth: 220 } },
            grid: { xaxis: { lines: { show: false } }, yaxis: { lines: { show: false } }, padding: { right: 16 } },
            dataLabels: {
                enabled: true,
                offsetX: 30,
                style: { colors: [CHART_INK.primary], fontSize: "12px", fontWeight: 600 },
                formatter: (_v, { dataPointIndex }) => `${reasons[dataPointIndex].pct}%`,
            },
            legend: { show: false },
            responsive: narrowCategoryLabels(Math.max(...reasons.map((r) => r.count), 1) * 1.35),
            tooltip: {
                custom: ({ dataPointIndex }) => {
                    const r = reasons[dataPointIndex];
                    return tooltipBox(r.label, [
                        [COLORS.groups[r.group], r.group_label, ""],
                        [null, "bajas", r.count],
                        [null, "del total", `${r.pct}%`],
                    ]);
                },
            },
        };

        const departments = data.departments;
        const departmentsChart = {
            chart: {
                type: "bar",
                events: {
                    dataPointSelection: (_e, _c, { dataPointIndex }) => {
                        const d = departments[dataPointIndex];
                        this.openEmployees(d.employee_ids, `Bajas · ${d.name}`);
                    },
                },
            },
            series: [{ name: "Bajas", data: departments.map((d) => d.exits) }],
            colors: [COLORS.departments],
            plotOptions: { bar: { horizontal: true, barHeight: "22px", borderRadius: 4, borderRadiusApplication: "end", dataLabels: { position: "top" } } },
            xaxis: { ...AXIS, categories: departments.map((d) => d.name), labels: { show: false } },
            // La escala deja ~35% de aire al final para que la etiqueta quepa fuera de la barra
            yaxis: { max: Math.max(...departments.map((d) => d.exits), 1) * 1.35, labels: { style: { colors: CHART_INK.secondary, fontSize: "13px" }, maxWidth: 220 } },
            grid: { xaxis: { lines: { show: false } }, yaxis: { lines: { show: false } }, padding: { right: 16 } },
            dataLabels: {
                enabled: true,
                offsetX: 44,
                style: { colors: [CHART_INK.primary], fontSize: "12px", fontWeight: 600 },
                formatter: (_v, { dataPointIndex }) => `${departments[dataPointIndex].exits} · ${departments[dataPointIndex].rate}%`,
            },
            legend: { show: false },
            responsive: narrowCategoryLabels(Math.max(...departments.map((d) => d.exits), 1) * 1.6),
            tooltip: {
                custom: ({ dataPointIndex }) => {
                    const d = departments[dataPointIndex];
                    return tooltipBox(d.name, [
                        [COLORS.departments, "bajas", d.exits],
                        [null, "rotación del área", `${d.rate}%`],
                        [null, "plantilla promedio", d.average_headcount],
                    ]);
                },
            },
        };

        const tenure = data.tenure;
        const tenureChart = {
            chart: {
                type: "bar",
                events: {
                    dataPointSelection: (_e, _c, { dataPointIndex }) => {
                        const t = tenure[dataPointIndex];
                        if (t.count) {
                            this.openEmployees(t.employee_ids, `Antigüedad · ${t.label}`);
                        }
                    },
                },
            },
            series: [{ name: "Empleados", data: tenure.map((t) => t.count) }],
            colors: COLORS.tenure,
            plotOptions: { bar: { distributed: true, columnWidth: "24px", borderRadius: 4, borderRadiusApplication: "end", dataLabels: { position: "top" } } },
            xaxis: { ...AXIS, categories: tenure.map((t) => t.label) },
            yaxis: { show: false },
            grid: { yaxis: { lines: { show: false } } },
            dataLabels: { enabled: true, offsetY: -20, style: { colors: [CHART_INK.primary], fontSize: "12px", fontWeight: 600 } },
            legend: { show: false },
            tooltip: {
                custom: ({ dataPointIndex }) => {
                    const t = tenure[dataPointIndex];
                    const total = tenure.reduce((s, x) => s + x.count, 0);
                    return tooltipBox(t.label, [
                        [COLORS.tenure[dataPointIndex], "empleados", t.count],
                        [null, "de la plantilla", `${total ? Math.round((t.count / total) * 100) : 0}%`],
                    ]);
                },
            },
        };

        return {
            headcount,
            movement,
            reasons: reasonsChart,
            reasonsHeight: Math.max(160, reasons.length * 44 + 30),
            departments: departmentsChart,
            departmentsHeight: Math.max(160, departments.length * 40 + 30),
            tenure: tenureChart,
        };
    }
}
