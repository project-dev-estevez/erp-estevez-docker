/** @odoo-module */
import { Component, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class KpiChartCard extends Component {
    static template = "hr_estevez.KpiChartCard";
    static props = {
        value: { type: Number },
        label: { type: String },
        icon: { type: String, optional: true },
        color: { type: String, optional: true },
        subtitle: { type: String, optional: true },
        tooltip: { type: String, optional: true },
        series: { type: Array, optional: true },
        labels: { type: Array, optional: true }, // ✅ NUEVO: Etiquetas para el eje X
        onClick: { type: Function, optional: true },
        onPointClick: { type: Function, optional: true }, // ✅ NUEVO: Click en punto específico
        isLoading: { type: Boolean, optional: true },
    };

    setup() {
        this.chartRef = useRef("chart");
        this.chartInstance = null;
        this.isPointClicked = false; // ✅ NUEVO: Flag para detectar click en punto

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

    get formattedValue() {
        return (this.props.value || 0).toLocaleString("es-MX");
    }

    onCardKeydown(ev) {
        if ((ev.key === "Enter" || ev.key === " ") && this.hasClick) {
            ev.preventDefault();
            this.props.onClick();
        }
    }

    onCardClick() {
        // ✅ NUEVO: Solo ejecutar si NO se hizo click en un punto
        if (this.hasClick && !this.isPointClicked) {
            this.props.onClick();
        }
        // ✅ Resetear el flag después de un pequeño delay
        setTimeout(() => {
            this.isPointClicked = false;
        }, 200); // ✅ Aumentamos el timeout
    }

    renderChart() {
        const options = {
            chart: {
                type: "area",
                height: 40, // ✅ Cabe en el pie de la tarjeta, como el texto de contexto de las demás
                sparkline: { enabled: true }, // ✅ VOLVER: Habilitar sparkline para gráfica limpia
                toolbar: { show: false },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        // ✅ NUEVO: Marcar que se hizo click en un punto
                        this.isPointClicked = true;

                        // ✅ NUEVO: Manejar click en punto específico
                        if (this.props.onPointClick) {
                            const dayIndex = config.dataPointIndex;
                            const dayName = this.props.labels && this.props.labels[dayIndex] 
                                ? this.props.labels[dayIndex] 
                                : `Día ${dayIndex + 1}`;
                            this.props.onPointClick(dayIndex, dayName);
                        }
                    }
                }
            },
            stroke: { curve: "smooth", width: 2 }, // ✅ Mantener línea fina
            fill: { 
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.3, // ✅ Más transparente para espacio reducido
                    opacityTo: 0.1,
                    stops: [0, 100]
                }
            },
            series: [{
                name: "Empleados",
                data: this.props.series || [0, 0, 0, 0, 0, 0, 0]
            }],
            colors: [getComputedStyle(this.chartRef.el).getPropertyValue("--o-hr-kpi-accent").trim() || "#008FFB"],
            xaxis: { 
                labels: { show: false }, 
                axisTicks: { show: false }, 
                axisBorder: { show: false },
                categories: this.props.labels || ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'] // ✅ Para el tooltip
            },
            yaxis: { 
                labels: { show: false }, 
                axisTicks: { show: false }, 
                axisBorder: { show: false }, 
                min: 0 
            },
            dataLabels: { enabled: false },
            grid: { show: false },
            tooltip: {
                enabled: true, // ✅ NUEVO: Habilitar tooltip
                custom: ({ series, seriesIndex, dataPointIndex, w }) => {
                    const value = series[seriesIndex][dataPointIndex];
                    const dayName = this.props.labels && this.props.labels[dataPointIndex] 
                        ? this.props.labels[dataPointIndex] 
                        : `Día ${dataPointIndex + 1}`;
                    
                    return `<div class="custom-tooltip" style="
                        background: rgba(0, 0, 0, 0.85); 
                        color: white; 
                        padding: 6px 10px; 
                        border-radius: 4px; 
                        font-size: 11px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
                        white-space: nowrap;
                    ">
                        <strong>${dayName}</strong> - ${value} ${value === 1 ? "alta" : "altas"}
                    </div>`;
                }
            }
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
