/** @odoo-module **/
import { Component, onWillStart, onWillUnmount, useEffect, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

const APEXCHARTS_URL = "https://cdn.jsdelivr.net/npm/apexcharts@3.45.2/dist/apexcharts.min.js";

// Ink y chrome comunes a todas las gráficas del dashboard de Dirección
export const CHART_INK = {
    primary: "#0b0b0b",
    secondary: "#52514e",
    muted: "#898781",
    grid: "#e1e0d9",
    axis: "#c3c2b7",
};

/**
 * Envoltura mínima de ApexCharts: recibe un objeto de opciones ya armado y
 * se redibuja solo cuando cambia ese objeto (no en cada render del padre).
 */
export class ExecChart extends Component {
    static template = "hr_estevez.ExecChart";
    static props = {
        options: Object,
        height: { type: Number, optional: true },
        ariaLabel: { type: String, optional: true },
    };

    setup() {
        this.chartRef = useRef("chart");
        this.chart = null;
        onWillStart(() => loadJS(APEXCHARTS_URL));
        useEffect(() => this.draw(), () => [this.props.options]);
        onWillUnmount(() => this.chart && this.chart.destroy());
    }

    draw() {
        const options = this.props.options;
        const config = {
            ...options,
            chart: {
                fontFamily: "inherit",
                foreColor: CHART_INK.muted,
                toolbar: { show: false },
                zoom: { enabled: false },
                animations: { enabled: true, speed: 300 },
                ...options.chart,
                height: this.props.height || 260,
            },
            grid: { borderColor: CHART_INK.grid, strokeDashArray: 0, ...(options.grid || {}) },
        };
        if (this.chart) {
            this.chart.updateOptions(config, true, true);
        } else {
            this.chart = new window.ApexCharts(this.chartRef.el, config);
            this.chart.render();
        }
    }
}
