/** @odoo-module */
import { loadJS } from "@web/core/assets";
const { Component, useRef, onMounted, onWillUnmount } = owl;

export class KpiChartCard extends Component {
    setup() {
        this.chartRef = useRef("chart");
        this.chartInstance = null;

        onMounted(async () => {
            await loadJS("https://cdn.jsdelivr.net/npm/apexcharts@3.45.2/dist/apexcharts.min.js");
            this.renderChart();
        });
        onWillUnmount(() => this.destroyChart());
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
                data: this.props.series || [100, 121, 139, 122, 90, 124, 180]
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
KpiChartCard.template = "hr_estevez.KpiChartCard";
