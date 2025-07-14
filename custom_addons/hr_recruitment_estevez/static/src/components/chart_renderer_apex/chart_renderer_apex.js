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

        // ✅ CORREGIR: Determinar si es horizontal basado en el tipo
        const isHorizontal = this.props.type === 'bar-horizontal';
        const chartType = isHorizontal ? 'bar' : (this.props.type || 'bar');

        // Configuración base de ApexCharts
        const defaultOptions = {
            chart: {
                type: chartType,  // Siempre 'bar', el horizontal se controla en plotOptions
                height: this.props.height || 350,
                width: '100%',    // ✅ AGREGAR: Asegurar ancho
                toolbar: {
                    show: false
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800
                }
            },
            plotOptions: {
                bar: {
                    horizontal: isHorizontal,  // ✅ CORREGIR: Usar variable calculada
                    borderRadius: 4,
                    columnWidth: '60%',
                    barHeight: '70%'  // ✅ AGREGAR: Para barras horizontales
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            xaxis: {
                categories: config.categories || [],
                labels: {
                    show: true
                }
            },
            yaxis: {
                title: {
                    text: config.yAxisTitle || ''
                }
            },
            fill: {
                opacity: 1
            },
            tooltip: {
                theme: 'light'
            },
            colors: config.colors || ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1'],
            // ✅ AGREGAR: Configuración específica para responsive
            responsive: [{
                breakpoint: 480,
                options: {
                    chart: {
                        width: 200
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }]
        };

        // Merger configuración personalizada
        const options = this.mergeDeep(defaultOptions, config.options || {});

        // ✅ VALIDAR: Asegurar que series tiene datos válidos
        const validSeries = config.series || [];
        if (validSeries.length === 0) {
            console.log("⚠️ No hay series válidas para renderizar");
            return;
        }

        // Configuración final
        const chartConfig = {
            ...options,
            series: validSeries
        };

        // ✅ DEBUG: Logs de depuración
        console.log("🔍 DEBUG ApexChart - Config completa:", chartConfig);
        console.log("🔍 DEBUG ApexChart - Series:", validSeries);
        console.log("🔍 DEBUG ApexChart - Elemento DOM:", this.chartRef.el);

        // ✅ VALIDAR: Asegurar que el elemento tiene dimensiones
        if (this.chartRef.el.offsetWidth === 0 || this.chartRef.el.offsetHeight === 0) {
            console.log("⚠️ El contenedor no tiene dimensiones válidas, reintentando...");
            setTimeout(() => this.renderChart(), 100);
            return;
        }

        try {
            // Crear la instancia de ApexChart
            this.chartInstance = new ApexCharts(this.chartRef.el, chartConfig);
            this.chartInstance.render();
            console.log("✅ ApexChart renderizado exitosamente");
        } catch (error) {
            console.error("❌ Error renderizando ApexChart:", error);
            console.log("📊 Configuración que causó el error:", chartConfig);
        }
    }

    updateChart() {
        if (!this.chartInstance) {
            this.renderChart();
            return;
        }

        const config = this.props.config || {};
        
        if (config.series) {
            console.log("🔄 Actualizando datos de ApexChart");
            this.chartInstance.updateSeries(config.series);
        }
        
        if (config.categories) {
            this.chartInstance.updateOptions({
                xaxis: {
                    categories: config.categories
                }
            });
        }
    }

    destroyChart() {
        if (this.chartInstance) {
            console.log("🗑️ Destruyendo instancia de ApexChart");
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
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
}

ChartRendererApex.template = "owl.ChartRendererApex";