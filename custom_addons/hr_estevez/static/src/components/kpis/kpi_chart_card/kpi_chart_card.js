/** @odoo-module */
import { Component, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class KpiChartCard extends Component {
    static template = "hr_estevez.KpiChartCard";
    static props = {
        value: { type: Number },
        label: { type: String },
        series: { type: Array, optional: true },
        onClick: { type: Function, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    setup() {
        this.chartRef = useRef("chart");
        this.chartInstance = null;

        onMounted(async () => {
            if (!this.props.isLoading) {
                await loadJS("https://cdn.jsdelivr.net/npm/apexcharts@3.45.2/dist/apexcharts.min.js");
                this.renderChart();
            }
        });
        onWillUnmount(() => this.destroyChart());
    }

    get hasClick() {
        return typeof this.props.onClick === 'function';
    }

    onCardClick() {
        if (this.hasClick) {
            this.props.onClick();
        }
    }

    renderChart() {
        const options = {
            chart: {
                type: "area",
                height: 80,
                sparkline: { enabled: true },
                toolbar: { show: false }
            },
            stroke: { curve: "smooth", width: 2 },
            fill: { opacity: 0.5 },
            series: [{
                name: "Empleados",
                data: this.props.series || [0, 0, 0, 0, 0, 0, 0]
            }],
            colors: ["#008FFB"],
            xaxis: { labels: { show: false }, axisTicks: { show: false }, axisBorder: { show: false } },
            yaxis: { labels: { show: false }, axisTicks: { show: false }, axisBorder: { show: false }, min: 0 },
            dataLabels: { enabled: false },
            grid: { show: false },
        };
        this.chartInstance = new window.ApexCharts(this.chartRef.el, options);
        this.chartInstance.render();
    }

    destroyChart() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }
}
