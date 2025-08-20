/** @odoo-module */

import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, onMounted, onWillUpdateProps, onWillUnmount } = owl

export class ChartRendererApex extends Component {
    setup(){
        this.chartRef = useRef("apexChart");
        this.chartInstance = null;
        
        onWillStart(async () => {
            await loadJS("https://cdn.jsdelivr.net/npm/apexcharts@3.45.2/dist/apexcharts.min.js");
        });

        onMounted(() => this.renderChart());
        onWillUpdateProps(() => this.updateChart());
        onWillUnmount(() => this.destroyChart());
    }

    renderChart() {
        if (!this.props.config?.series) {
            console.log("⚠️ No hay datos para renderizar ApexChart");
            return;
        }

        // Destruir instancia previa si existe
        this.destroyChart();

        const config = this.props.config || {};

        // Determinar si es horizontal basado en el tipo
        const isHorizontal = this.props.type === 'bar-horizontal';
        const chartType = isHorizontal ? 'bar' : (this.props.type || 'bar');

        // Configuración base de ApexCharts
        const defaultOptions = {
            chart: {
                type: chartType,
                height: this.props.height || 350,
                width: '100%',
                cursor: 'pointer',
                toolbar: {
                    show: true,
                },
                animations: {
                    enabled: true,
                },
            },
            plotOptions: {
                bar: {
                    horizontal: isHorizontal,
                },
            },
            dataLabels: {
                enabled: true,
            },
            xaxis: {
                categories: config.categories || [],
            },
            series: config.series || [],
        };

        const options = Object.assign({}, defaultOptions, config);

        this.chartInstance = new window.ApexCharts(this.chartRef.el, options);
        this.chartInstance.render();
    }

    updateChart() {
        if (this.chartInstance && this.props.config?.series) {
            this.chartInstance.updateOptions(this.props.config);
        } else {
            this.renderChart();
        }
    }

    destroyChart() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }
}

ChartRendererApex.template = "owl.ChartRendererApex";
