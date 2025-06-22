/** @odoo-module */

import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, onMounted, onWillUpdateProps } = owl

export class ChartRenderer extends Component {
    setup(){
        this.chartRef = useRef("chart");
        this.chartInstance = null;
        onWillStart(async ()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
            await loadJS("https://cdn.jsdelivr.net/npm/chartjs-chart-funnel@4.2.4/build/index.umd.min.js");
            await loadJS("https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js");
        })

        onMounted(()=>this.renderChart());
        onWillUpdateProps(() => this.renderChart());
    }

    renderChart() {
        if (window.Chart && window.Chart.register && window.ChartDataLabels) {
            window.Chart.register(window.ChartDataLabels);
        }
        // Destruye la instancia previa si existe
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }
        const config = this.props.config || {};
        const data = config.data || {};
        const defaultOptions = {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                title: {
                    display: true,
                    text: this.props.title,
                    position: 'bottom',
                }
            }
        };
        const options = {
            ...defaultOptions,
            ...(config.options || {}),
            plugins: {
                ...defaultOptions.plugins,
                ...(config.options?.plugins || {}),
                legend: {
                    ...defaultOptions.plugins.legend,
                    ...(config.options?.plugins?.legend || {}),
                },
                title: {
                    ...defaultOptions.plugins.title,
                    ...(config.options?.plugins?.title || {}),
                }
            }
        };
        this.chartInstance = new Chart(this.chartRef.el, {
            type: this.props.type,
            data: data,
            options: options,
        });
    }
}

ChartRenderer.template = "owl.ChartRenderer"