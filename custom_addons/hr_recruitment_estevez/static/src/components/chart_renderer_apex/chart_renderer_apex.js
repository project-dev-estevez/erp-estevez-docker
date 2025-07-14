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
                type: chartType,
                height: this.props.height || 350,
                width: '100%',
                toolbar: {
                    show: true,  // ✅ CAMBIO: Habilitar toolbar
                    offsetX: 0,
                    offsetY: 0,
                    tools: {
                        download: true,      // ✅ HABILITAR: Menú desplegable nativo
                        selection: false,
                        zoom: false,
                        zoomin: false,
                        zoomout: false,
                        pan: false,
                        reset: false
                    },
                    // ✅ CONFIGURACIÓN: Opciones de exportación
                    export: {
                        csv: {
                            filename: `${config.filename || 'grafica'}_datos`,
                            columnDelimiter: ',',
                            headerCategory: 'Categoría',
                            headerValue: 'Valor',
                            dateFormatter(timestamp) {
                                return new Date(timestamp).toDateString()
                            }
                        },
                        svg: {
                            filename: `${config.filename || 'grafica'}_imagen`,
                        },
                        png: {
                            filename: `${config.filename || 'grafica'}_imagen`,
                            width: undefined,    // Usar ancho del gráfico
                            height: undefined    // Usar altura del gráfico
                        }
                    },
                    // ✅ NUEVO: Auto-selected para mostrar menú desplegable
                    autoSelected: 'download'
                },
                // ✅ NUEVO: Eventos para personalizar descarga
                events: {
                    beforeExport: function (chartContext, options) {
                        console.log(`📥 Descargando ${options.type.toUpperCase()}: ${options.filename}`);

                        // Personalizar nombre según tipo
                        const fecha = new Date().toISOString().split('T')[0];
                        const baseFilename = config.filename || 'grafica';

                        if (options.type === 'csv') {
                            options.filename = `${baseFilename}_datos_${fecha}`;
                        } else {
                            options.filename = `${baseFilename}_imagen_${fecha}`;
                        }

                        return options;
                    },
                    exported: function (chartContext, options) {
                        console.log(`✅ ${options.type.toUpperCase()} descargado exitosamente: ${options.filename}`);
                    }
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800
                }
            },
            // ...resto de configuración sin cambios...
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