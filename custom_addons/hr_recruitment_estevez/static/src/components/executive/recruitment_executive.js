/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import {
    ExecChart, CHART_INK, AXIS, tooltipBox, narrowCategoryLabels,
} from "@hr_estevez/components/executive/exec_chart";

// Misma paleta validada que el dashboard de Empleados
const COLORS = {
    accent: "#2a78d6",
    muted: "#c3c2b7",
    decline: "#eb6834",
    company: "#2a78d6",
};

const SEVERITY_ICON = {
    critical: "fa-exclamation-circle",
    warning: "fa-exclamation-triangle",
    info: "fa-info-circle",
};

const RECRUITER_COLUMNS = [
    { key: "name", label: "Reclutador" },
    { key: "open_jobs", label: "Vacantes activas" },
    { key: "applicants", label: "Postulaciones" },
    { key: "hired", label: "Contratados" },
    { key: "conversion", label: "Conversión" },
    { key: "time_to_hire", label: "Días para contratar" },
    { key: "stalled", label: "Sin avanzar" },
];

export class RecruitmentExecutive extends Component {
    static template = "hr_recruitment_estevez.RecruitmentExecutive";
    static components = { ExecChart };
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.colors = COLORS;
        this.recruiterColumns = RECRUITER_COLUMNS;
        this.charts = {};
        this.state = useState({
            filters: { recruiterId: false, directionId: false, jobId: false },
            options: { recruiters: [], directions: [] },
            data: null,
            funnel: null,
            loading: true,
            funnelLoading: false,
            tables: {},
            sort: { key: "hired", desc: true },
        });
        onWillStart(async () => {
            this.state.options = await this.orm.call("hr.recruitment.executive.dashboard", "get_filter_options", []);
            await this.load(this.props);
        });
        onWillUpdateProps(async (next) => {
            if (next.startDate !== this.props.startDate || next.endDate !== this.props.endDate) {
                await this.load(next);
            }
        });
    }

    rangeArgs(props = this.props) {
        const { recruiterId, directionId } = this.state.filters;
        return [props.startDate, props.endDate, recruiterId, directionId];
    }

    async load(props = this.props) {
        if (!props.startDate || !props.endDate) {
            return;
        }
        this.state.loading = true;
        const data = await this.orm.call("hr.recruitment.executive.dashboard", "get_dashboard_data", this.rangeArgs(props));
        this.charts = this.buildCharts(data);
        this.state.data = data;
        this.state.funnel = data.funnel;
        // La vacante elegida puede no existir en el nuevo rango
        if (this.state.filters.jobId && !data.vacancies.some((v) => v.id === this.state.filters.jobId)) {
            this.state.filters.jobId = false;
        } else if (this.state.filters.jobId) {
            await this.loadFunnel(props);
        }
        this.state.loading = false;
    }

    async loadFunnel(props = this.props) {
        this.state.funnelLoading = true;
        this.state.funnel = await this.orm.call("hr.recruitment.executive.dashboard", "get_funnel",
            [...this.rangeArgs(props), this.state.filters.jobId]);
        this.state.funnelLoading = false;
    }

    // ---------- Filtros ----------
    onFilterChange(key, ev) {
        this.state.filters[key] = ev.target.value ? parseInt(ev.target.value) : false;
        this.load();
    }

    onVacancyChange(ev) {
        this.state.filters.jobId = ev.target.value ? parseInt(ev.target.value) : false;
        if (this.state.filters.jobId) {
            this.loadFunnel();
        } else {
            this.state.funnel = this.state.data.funnel;
        }
    }

    toggleTable(key) {
        this.state.tables[key] = !this.state.tables[key];
    }

    sortBy(key) {
        const sort = this.state.sort;
        sort.desc = sort.key === key ? !sort.desc : key !== "name";
        sort.key = key;
    }

    // ---------- Formato ----------
    get sortedRecruiters() {
        const { key, desc } = this.state.sort;
        const rows = [...this.state.data.recruiters];
        rows.sort((a, b) => {
            const x = a[key] ?? -1;
            const y = b[key] ?? -1;
            const cmp = typeof x === "string" ? x.localeCompare(y) : x - y;
            return desc ? -cmp : cmp;
        });
        return rows;
    }

    get maxConversion() {
        return Math.max(...this.state.data.recruiters.map((r) => r.conversion), 1);
    }

    sortIcon(key) {
        if (this.state.sort.key !== key) {
            return "fa-sort text-muted opacity-50";
        }
        return this.state.sort.desc ? "fa-sort-desc" : "fa-sort-asc";
    }

    funnelWidth(level) {
        return Math.max(level.overall_rate, 3);
    }

    days(value) {
        return value === null || value === undefined ? "—" : `${value.toLocaleString("es-MX")}`;
    }

    severityIcon(severity) {
        return SEVERITY_ICON[severity] || SEVERITY_ICON.info;
    }

    // ---------- Navegación ----------
    openApplicants(ids, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "hr.applicant",
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
    horizontalBars({ rows, values, colors, labels, shortLabels, tooltip, onClick, max, headroom = 1.35, offsetX = 30 }) {
        const top = Math.max(...values, 1) * headroom;
        const responsive = narrowCategoryLabels(top);
        if (shortLabels) {
            // En celular la etiqueta larga no cabe: solo el número (el detalle queda en tooltip y tabla)
            responsive[0].options.dataLabels = {
                ...responsive[0].options.dataLabels,
                offsetX: 18,
                formatter: (_v, { dataPointIndex }) => shortLabels(rows[dataPointIndex]),
            };
        }
        return {
            chart: {
                type: "bar",
                events: { dataPointSelection: (_e, _c, { dataPointIndex }) => onClick(rows[dataPointIndex]) },
            },
            series: [{ name: "valor", data: values }],
            colors,
            plotOptions: { bar: { horizontal: true, distributed: colors.length > 1, barHeight: "22px", borderRadius: 4, borderRadiusApplication: "end", dataLabels: { position: "top" } } },
            xaxis: { ...AXIS, categories: rows.map((r) => r.name || r.label), labels: { show: false } },
            yaxis: { max: max || top, labels: { style: { colors: CHART_INK.secondary, fontSize: "13px" }, maxWidth: 220 } },
            grid: { xaxis: { lines: { show: false } }, yaxis: { lines: { show: false } }, padding: { right: 16 } },
            dataLabels: {
                enabled: true,
                offsetX,
                style: { colors: [CHART_INK.primary], fontSize: "12px", fontWeight: 600 },
                formatter: (_v, { dataPointIndex }) => labels(rows[dataPointIndex]),
            },
            legend: { show: false },
            responsive,
            tooltip: { custom: ({ dataPointIndex }) => tooltip(rows[dataPointIndex]) },
        };
    }

    buildCharts(data) {
        const bottlenecks = data.bottlenecks;
        const sources = data.sources;
        const reasons = data.rejections.reasons;
        return {
            // Énfasis: la etapa más lenta en color, el resto en gris
            bottlenecks: this.horizontalBars({
                rows: bottlenecks,
                values: bottlenecks.map((b) => b.avg_days),
                colors: bottlenecks.map((_b, i) => (i === 0 ? COLORS.accent : COLORS.muted)),
                labels: (b) => `${b.avg_days} d`,
                tooltip: (b) => tooltipBox(b.name, [
                    [COLORS.accent, "días promedio", b.avg_days],
                    [null, "candidatos medidos", b.count],
                ]),
                onClick: () => {},
            }),
            bottlenecksHeight: Math.max(150, bottlenecks.length * 40 + 30),
            sources: this.horizontalBars({
                rows: sources,
                values: sources.map((s) => s.applicants),
                colors: [COLORS.accent],
                labels: (s) => `${s.applicants} · ${s.hired} contrat. (${s.effectiveness}%)`,
                shortLabels: (s) => `${s.applicants}`,
                headroom: 1.9,
                offsetX: 74,
                tooltip: (s) => tooltipBox(s.name, [
                    [COLORS.accent, "postulaciones", s.applicants],
                    [null, "contratados", s.hired],
                    [null, "efectividad", `${s.effectiveness}%`],
                ]),
                onClick: (s) => this.openApplicants(s.applicant_ids, `Postulaciones · ${s.name}`),
            }),
            sourcesHeight: Math.max(150, sources.length * 40 + 30),
            rejections: this.horizontalBars({
                rows: reasons,
                values: reasons.map((r) => r.count),
                colors: reasons.map((r) => (r.group === "candidato" ? COLORS.decline : COLORS.company)),
                labels: (r) => `${r.pct}%`,
                headroom: 1.2,
                tooltip: (r) => tooltipBox(r.label, [
                    [r.group === "candidato" ? COLORS.decline : COLORS.company,
                        r.group === "candidato" ? "el candidato declinó" : "la empresa rechazó", ""],
                    [null, "candidatos", r.count],
                    [null, "del total", `${r.pct}%`],
                ]),
                onClick: (r) => this.openApplicants(r.applicant_ids, `Rechazos · ${r.label}`),
            }),
            rejectionsHeight: Math.max(150, reasons.length * 40 + 30),
        };
    }
}
