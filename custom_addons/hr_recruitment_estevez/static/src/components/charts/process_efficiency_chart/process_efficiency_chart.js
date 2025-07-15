/** @odoo-module */

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class ProcessEfficiencyChart extends Component {
    static template = "hr_recruitment_estevez.ProcessEfficiencyChart";
    static components = { ChartRendererApex };
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
        title: { type: String, optional: true },
        height: { type: [String, Number], optional: true },
        onMounted: { type: Function, optional: true }
    };

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            chartData: null,
            isLoading: true,
            centerValue: '0d',
            hasData: false  // ✅ NUEVO: Indicador de si hay datos reales
        });

        onWillStart(async () => {
            await this.loadChart();
        });

        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });
    }

    async loadChart() {
        console.log("📊 ProcessEfficiencyChart: Cargando datos reales...", {
            startDate: this.props.startDate,
            endDate: this.props.endDate
        });

        this.state.isLoading = true;

        try {
            await this.calculateAverageTimePerStage();
            console.log("✅ ProcessEfficiencyChart: Proceso de carga completado");
        } catch (error) {
            console.error("❌ ProcessEfficiencyChart: Error cargando datos:", error);
            // ✅ CAMBIO: En caso de error, mostrar gráfica vacía
            this.showEmptyChart();
        } finally {
            this.state.isLoading = false;
        }
    }

    // ✅ MÉTODO PRINCIPAL: Calcular tiempo promedio por etapa (basado en dashboard)
    async calculateAverageTimePerStage() {
        console.log("📊 ProcessEfficiencyChart: Calculando tiempo promedio por etapa (solo contratados)...");
        
        // 1) Obtener applicants contratados en el rango de fechas
        let hiredDomain = [["application_status", "=", "hired"]];
        hiredDomain = this._getHiredDateRangeDomain(hiredDomain);
        
        const hiredApplicants = await this.orm.searchRead(
            "hr.applicant",
            hiredDomain,
            ["id"]
        );
        
        console.log("👥 ProcessEfficiencyChart: Applicants contratados encontrados:", hiredApplicants.length);
        
        // ✅ CAMBIO: Si no hay contratados, mostrar gráfica vacía
        if (hiredApplicants.length === 0) {
            console.log("⚠️ ProcessEfficiencyChart: No hay contratados en este rango, mostrando gráfica vacía");
            this.showEmptyChart();
            return;
        }
        
        // 2) Obtener IDs de los applicants contratados
        const hiredIds = hiredApplicants.map(a => a.id);
        
        // 3) Consultar historial con duración en horas
        const historyRecords = await this.orm.searchRead(
            "hr.applicant.stage.history",
            [
                ['applicant_id', 'in', hiredIds],
                ['leave_date', '!=', false],
                ['duration_hours', '>', 0]
            ],
            ['stage_id', 'duration_days', 'duration_hours', 'applicant_id']
        );
        
        console.log("📈 ProcessEfficiencyChart: Registros de historial:", historyRecords.length);
        
        // 4) Agrupar por etapa
        const stageTimeMap = {};
        
        for (const record of historyRecords) {
            const stageId = record.stage_id[0];
            const stageName = record.stage_id[1];
            
            if (!stageTimeMap[stageId]) {
                stageTimeMap[stageId] = {
                    name: stageName,
                    durations: []
                };
            }
            
            stageTimeMap[stageId].durations.push({
                days: record.duration_days,
                hours: record.duration_hours
            });
        }
        
        // 5) Calcular promedios
        const stageData = [];
        let totalHours = 0;
        let totalCount = 0;
        
        for (const stageId in stageTimeMap) {
            const stage = stageTimeMap[stageId];
            const durations = stage.durations;
            
            if (durations.length > 0) {
                const avgHours = durations.reduce((sum, d) => sum + d.hours, 0) / durations.length;
                const avgDays = avgHours / 24;
                
                stageData.push({
                    name: stage.name,
                    days: Number(avgDays.toFixed(2)),
                    hours: avgHours,
                    count: durations.length
                });
                
                totalHours += avgHours * durations.length;
                totalCount += durations.length;
                
                console.log(`📋 ${stage.name}: ${avgDays.toFixed(2)} días promedio (${durations.length} muestras)`);
            }
        }
        
        // ✅ CAMBIO: Si no hay datos de etapas válidos, mostrar gráfica vacía
        if (stageData.length === 0) {
            console.log("⚠️ ProcessEfficiencyChart: No hay datos de etapas válidos, mostrando gráfica vacía");
            this.showEmptyChart();
            return;
        }
        
        // ✅ ÉXITO: Hay datos reales, configurar gráfico
        this.state.hasData = true;
        
        // 7) Ordenar por tiempo promedio (descendente)
        stageData.sort((a, b) => b.days - a.days);
        
        // 8) Formatear el promedio global
        const globalAverageHours = totalCount > 0 ? (totalHours / totalCount) : 0;
        let centerText = "0d";
        
        if (globalAverageHours >= 24) {
            const days = (globalAverageHours / 24).toFixed(1);
            centerText = `${days}d`;
        } else if (globalAverageHours >= 1) {
            const hours = globalAverageHours.toFixed(1);
            centerText = `${hours}h`;
        } else if (globalAverageHours > 0) {
            const minutes = Math.round(globalAverageHours * 60);
            centerText = `${minutes}m`;
        }
        
        // 9) Preparar datos para ApexCharts
        const labels = stageData.map(s => {
            const days = s.days;
            let timeText = "";
            if (days >= 1) {
                timeText = `(${days.toFixed(1)}d)`;
            } else if (s.hours >= 1) {
                timeText = `(${s.hours.toFixed(1)}h)`;
            } else {
                const minutes = Math.round(s.hours * 60);
                timeText = `(${minutes}m)`;
            }
            return `${s.name} ${timeText}`;
        });
        
        const series = stageData.map(s => s.days);
        const colors = this.getPastelColors(stageData.length);
        
        // 10) Configurar gráfico con datos reales
        this.state.chartData = {
            series: series,
            options: {
                chart: {
                    type: 'donut',
                    height: this.props.height || 350,
                    events: {
                        dataPointSelection: (event, chartContext, config) => {
                            const stageInfo = stageData[config.dataPointIndex];
                            console.log('🔍 Click en etapa:', stageInfo);
                        }
                    }
                },
                labels: labels,
                colors: colors,
                plotOptions: {
                    pie: {
                        donut: { 
                            size: '70%',
                            labels: {
                                show: true,
                                name: {
                                    show: true,
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#6c757d',
                                    offsetY: -10,
                                    formatter: function () {
                                        return 'Promedio Total';
                                    }
                                },
                                value: {
                                    show: true,
                                    fontSize: '32px',
                                    fontWeight: 'bold',
                                    color: '#0d6efd',
                                    offsetY: 10,
                                    formatter: function (val) {
                                        return centerText;
                                    }
                                },
                                total: {
                                    show: true,
                                    showAlways: true,
                                    label: 'Promedio Total',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#6c757d',
                                    formatter: function (w) {
                                        return centerText;
                                    }
                                }
                            }
                        },
                        startAngle: -90,
                        endAngle: 270
                    }
                },
                legend: { 
                    position: 'bottom',
                    horizontalAlign: 'center',
                    fontSize: '12px'
                },
                dataLabels: { 
                    enabled: true,
                    formatter: function (val, opts) {
                        const stageInfo = stageData[opts.seriesIndex];
                        const days = stageInfo.days;
                        if (days >= 1) {
                            return `${days.toFixed(1)}d`;
                        } else if (stageInfo.hours >= 1) {
                            return `${stageInfo.hours.toFixed(1)}h`;
                        } else {
                            const minutes = Math.round(stageInfo.hours * 60);
                            return `${minutes}m`;
                        }
                    },
                    style: {
                        fontSize: '11px',
                        fontWeight: 'bold',
                        colors: ['#fff']
                    },
                    dropShadow: {
                        enabled: false
                    }
                },
                title: {
                    text: this.props.title || 'Eficiencia del Proceso de Contratación',
                    align: 'center',
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }
                },
                tooltip: {
                    enabled: true,
                    y: {
                        formatter: function(val, opts) {
                            const stageInfo = stageData[opts.seriesIndex];
                            const days = stageInfo.days;
                            const hours = stageInfo.hours;
                            const count = stageInfo.count;
                            
                            let timeText = "";
                            if (days >= 1) {
                                timeText = `${days.toFixed(1)} días`;
                            } else if (hours >= 1) {
                                timeText = `${hours.toFixed(1)} horas`;
                            } else {
                                const minutes = Math.round(hours * 60);
                                timeText = `${minutes} minutos`;
                            }
                            
                            return `${timeText} promedio (${count} candidatos contratados)`;
                        }
                    }
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shade: 'light',
                        type: 'horizontal',
                        shadeIntensity: 0.25
                    }
                },
                stroke: {
                    width: 2,
                    colors: ['#fff']
                },
                responsive: [{
                    breakpoint: 480,
                    options: {
                        chart: {
                            height: 300
                        },
                        legend: {
                            position: 'bottom',
                            fontSize: '10px'
                        },
                        plotOptions: {
                            pie: {
                                donut: {
                                    labels: {
                                        name: {
                                            fontSize: '12px'
                                        },
                                        value: {
                                            fontSize: '24px'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }]
            }
        };

        this.state.centerValue = centerText;
        
        console.log("✅ ProcessEfficiencyChart: Gráfico real configurado - Promedio global:", centerText);
        console.log("🎯 Basado en", hiredApplicants.length, "candidatos contratados");
    }

    // ✅ NUEVO: Mostrar gráfica vacía cuando no hay datos
    showEmptyChart() {
        console.log("📊 ProcessEfficiencyChart: Configurando gráfica vacía (sin datos)");
        
        this.state.hasData = false;
        this.state.centerValue = '0d';
        
        this.state.chartData = {
            series: [],  // ✅ Array vacío = gráfica vacía
            options: {
                chart: {
                    type: 'donut',
                    height: this.props.height || 350,
                },
                labels: [],  // ✅ Sin etiquetas
                colors: [],  // ✅ Sin colores
                plotOptions: {
                    pie: {
                        donut: { 
                            size: '70%',
                            labels: {
                                show: true,
                                name: {
                                    show: true,
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#6c757d',
                                    offsetY: -10,
                                    formatter: function () {
                                        return 'Sin Datos';
                                    }
                                },
                                value: {
                                    show: true,
                                    fontSize: '32px',
                                    fontWeight: 'bold',
                                    color: '#dc3545',  // ✅ Color rojo para indicar sin datos
                                    offsetY: 10,
                                    formatter: function (val) {
                                        return '0d';
                                    }
                                },
                                total: {
                                    show: true,
                                    showAlways: true,
                                    label: 'Sin Datos',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#6c757d',
                                    formatter: function (w) {
                                        return '0d';
                                    }
                                }
                            }
                        },
                        startAngle: -90,
                        endAngle: 270
                    }
                },
                legend: { 
                    position: 'bottom',
                    horizontalAlign: 'center',
                    fontSize: '12px'
                },
                dataLabels: { 
                    enabled: false  // ✅ Sin etiquetas de datos
                },
                title: {
                    text: this.props.title || 'Eficiencia del Proceso de Contratación',
                    align: 'center',
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }
                },
                tooltip: {
                    enabled: true,
                    custom: function({series, seriesIndex, dataPointIndex, w}) {
                        return '<div class="custom-tooltip">' +
                               '<span>No hay datos disponibles en el rango de fechas seleccionado</span>' +
                               '</div>';
                    }
                },
                noData: {
                    text: 'No hay candidatos contratados en el rango de fechas seleccionado',
                    align: 'center',
                    verticalAlign: 'middle',
                    offsetX: 0,
                    offsetY: 0,
                    style: {
                        color: '#6c757d',
                        fontSize: '14px',
                        fontFamily: undefined
                    }
                }
            }
        };
    }

    // ✅ ELIMINAR COMPLETAMENTE: loadMockData() (ya no se usa)
    // async loadMockData() { ... }  // ❌ ELIMINAR

    // ✅ Métodos de filtrado por fechas (mantener)
    _getHiredDateRangeDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["date_closed", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["date_closed", "<=", this.props.endDate]);
        }
        return domain;
    }

    // ✅ Método para generar colores (mantener)
    getPastelColors(count) {
        const premiumColors = [
            '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB347',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#FF6B6B',
        ];

        if (count <= premiumColors.length) {
            return premiumColors.slice(0, count);
        }

        const colors = [...premiumColors];
        for (let i = premiumColors.length; i < count; i++) {
            const hue = Math.floor((360 / (count - premiumColors.length)) * (i - premiumColors.length));
            const saturation = 65 + Math.random() * 20;
            const lightness = 55 + Math.random() * 20;
            colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }
        
        return colors;
    }

    // ✅ Método público para recargar datos (mantener)
    async refresh() {
        await this.loadChart();
    }
}