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
        const config = this.props.config || {};
        
        // Verificar si hay series (puede venir directamente en config o en config.series)
        const hasSeries = config.series || (config.chart && config.series !== undefined);
        if (!hasSeries) {
            console.log("⚠️ No hay datos para renderizar ApexChart");
            return;
        }

        // Destruir instancia previa si existe
        this.destroyChart();

        // Determinar si es horizontal basado en el tipo
        const isHorizontal = this.props.type === 'bar-horizontal';
        const chartType = isHorizontal ? 'bar' : (this.props.type || 'bar');

        // Obtener filename desde config o props
        const filename = config.filename || this.props.filename || 'chart_export';

        // Configuración base solo con título y toolbar
        const titleAndToolbar = {
            chart: {
                type: chartType,
                toolbar: {
                    show: true,
                    offsetX: 0,
                    offsetY: 0,
                    tools: {
                        download: true,
                        selection: false,
                        zoom: false,
                        zoomin: false,
                        zoomout: false,
                        pan: false,
                        reset: false,
                    },
                    export: {
                        csv: {
                            filename: filename,
                            columnDelimiter: ',',
                            headerCategory: 'Categoría',
                            headerValue: 'Valor',
                        },
                        svg: {
                            filename: filename,
                        },
                        png: {
                            filename: filename,
                        }
                    },
                },
            },
            title: {
                text: this.props.title || '',
                align: 'center',
                style: {
                    fontSize: '16px',
                    fontWeight: 600,
                    color: '#263238'
                }
            },
        };

        // Merge: título/toolbar + config existente
        const options = this.mergeDeep(titleAndToolbar, config);

        this.chartInstance = new window.ApexCharts(this.chartRef.el, options);
        this.chartInstance.render();
    }

    // Utility para hacer merge profundo de objetos
    mergeDeep(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target))
                        Object.assign(output, { [key]: source[key] });
                    else
                        output[key] = this.mergeDeep(target[key], source[key]);
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }

    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
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

ChartRendererApex.template = "hr_estevez.ChartRenderApexHR";
