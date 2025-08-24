/** @odoo-module */
import { Component, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class KpiChartCard extends Component {
    static template = "hr_estevez.KpiChartCard";
    static props = {
        value: { type: Number },
        label: { type: String },
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

    onCardClick() {
        console.log("🖱️ Click en card, isPointClicked:", this.isPointClicked);
        // ✅ NUEVO: Solo ejecutar si NO se hizo click en un punto
        if (this.hasClick && !this.isPointClicked) {
            console.log("✅ Ejecutando click general de card");
            this.props.onClick();
        } else if (this.isPointClicked) {
            console.log("❌ Click bloqueado porque se hizo click en punto");
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
                height: 80,
                sparkline: { enabled: true }, // ✅ VOLVER: Habilitar sparkline para gráfica limpia
                toolbar: { show: false },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        // ✅ NUEVO: Marcar que se hizo click en un punto
                        this.isPointClicked = true;
                        console.log("🎯 Click en punto específico:", config.dataPointIndex);
                        
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
            stroke: { curve: "smooth", width: 2 },
            fill: { opacity: 0.5 },
            series: [{
                name: "Empleados",
                data: this.props.series || [0, 0, 0, 0, 0, 0, 0]
            }],
            colors: ["#008FFB"],
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
                        background: rgba(0, 0, 0, 0.8); 
                        color: white; 
                        padding: 8px 12px; 
                        border-radius: 6px; 
                        font-size: 12px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    ">
                        <strong>${dayName}</strong><br/>
                        Empleados: <strong>${value}</strong>
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
