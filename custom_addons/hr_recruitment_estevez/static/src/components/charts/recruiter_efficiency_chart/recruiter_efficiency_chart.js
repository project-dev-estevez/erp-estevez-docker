/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";  // ✅ Agregar onMounted
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class RecruiterEfficiencyChart extends Component {
    static template = "hr_recruitment_estevez.RecruiterEfficiencyChart";
    static components = { ChartRendererApex };
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
        title: { type: String, optional: true },
        height: { type: [String, Number], optional: true },
        onMounted: { type: Function, optional: true },  // ✅ NUEVO: Callback prop
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        // ✅ Estado local para los datos del gráfico
        this.state = useState({
            chartData: {
                series: [],
                categories: [],
                colors: ['#80c7fd', '#00E396'],
                meta: [],
                filename: 'eficiencia_reclutadores',
                options: {}
            },
            isLoading: true
        });

        // ✅ Cargar datos al inicializar
        onWillStart(async () => {
            await this.loadChartData();
        });

        // ✅ NUEVO: Notificar al componente padre cuando se monte
        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });
    }

    // ✅ Método público para recargar datos
    async loadChartData() {
        console.log("📊 RecruiterEfficiencyChart: Cargando datos...", {
            startDate: this.props.startDate,
            endDate: this.props.endDate
        });
        this.state.isLoading = true;

        try {
            await this.calculateRecruiterStats();
            console.log("✅ RecruiterEfficiencyChart: Datos cargados exitosamente");
        } catch (error) {
            console.error("❌ RecruiterEfficiencyChart: Error cargando datos:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    // ✅ Resto del código sin cambios...
    async calculateRecruiterStats() {
        // 1. Total postulaciones por reclutador (por create_date)
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);

        const totalData = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        // 2. Contratados por reclutador (por date_closed)
        let hiredDomain = [
            ["application_status", "=", "hired"]
        ];
        hiredDomain = this._getHiredDateRangeDomain(hiredDomain);

        const hiredData = await this.orm.readGroup(
            "hr.applicant",
            hiredDomain,
            ["user_id"],
            ["user_id"]
        );

        // 3. En proceso por reclutador (ongoing)
        let ongoingDomain = [
            ["application_status", "=", "ongoing"]
        ];
        ongoingDomain = this._addDateRangeToDomain(ongoingDomain);

        const ongoingData = await this.orm.readGroup(
            "hr.applicant",
            ongoingDomain,
            ["user_id"],
            ["user_id"]
        );

        // 4. Unir todos los conjuntos de usuarios
        const recruiterMap = {};

        // Total postulaciones
        for (const r of totalData) {
            const id = (r.user_id && r.user_id[0]) || false;
            const name = (r.user_id && r.user_id[1]) || "Desconocido";
            recruiterMap[id] = {
                id,
                name,
                total: r.user_id_count,
                hired: 0,
                ongoing: 0
            };
        }

        // Contratados
        for (const r of hiredData) {
            const id = (r.user_id && r.user_id[0]) || false;
            const name = (r.user_id && r.user_id[1]) || "Desconocido";
            if (!recruiterMap[id]) {
                recruiterMap[id] = { id, name, total: 0, hired: 0, ongoing: 0 };
            }
            recruiterMap[id].hired = r.user_id_count;
        }

        // En proceso
        for (const r of ongoingData) {
            const id = (r.user_id && r.user_id[0]) || false;
            const name = (r.user_id && r.user_id[1]) || "Desconocido";
            if (!recruiterMap[id]) {
                recruiterMap[id] = { id, name, total: 0, hired: 0, ongoing: 0 };
            }
            recruiterMap[id].ongoing = r.user_id_count;
        }

        // 5. Construir el array final
        const recruiterStats = Object.values(recruiterMap).map(r => {
            const percentage = r.total > 0 ? ((r.hired / r.total) * 100).toFixed(2) : "0.00";
            return { ...r, percentage };
        });

        // 6. ✅ SIMPLE: Preparar datos SIN duplicar categorías
        const labels = recruiterStats.map(r => r.name);
        const ongoingCounts = recruiterStats.map(r => r.ongoing);
        const hiredCounts = recruiterStats.map(r => r.hired);
        const totalCounts = recruiterStats.map(r => r.total);  // ✅ NUEVA serie

        console.log("📊 Labels:", labels);
        console.log("📊 OngoingCounts:", ongoingCounts);
        console.log("📊 HiredCounts:", hiredCounts);
        console.log("📊 TotalCounts:", totalCounts);

        // 7. ✅ CONFIGURAR: Tres series con Total separado
        this.state.chartData = {
            series: [
                {
                    name: 'Total Postulaciones',
                    data: totalCounts,
                    stack: 'total'   // ✅ CAMBIAR: Darle su propio stack
                },
                {
                    name: 'En Proceso',
                    data: ongoingCounts,
                    stack: 'detalle'
                },
                {
                    name: 'Contratados',
                    data: hiredCounts,
                    stack: 'detalle'
                }
            ],
            categories: labels,
            colors: ['#FFD700', '#00E396', '#3f51b5'],  // ✅ Tres colores
            meta: recruiterStats,
            filename: 'eficiencia_reclutadores',
            options: {
                chart: {
                    type: 'bar',
                    stacked: true,  // ✅ Mantener apilado solo para las que tienen stack
                    height: this.props.height || 400,
                    events: {
                        dataPointSelection: (event, chartContext, config) => {
                            const seriesIndex = config.seriesIndex;
                            const dataPointIndex = config.dataPointIndex;
                            const stat = recruiterStats[dataPointIndex];

                            // ✅ CORREGIR: Índices según el nuevo orden
                            let onlyHired = false;
                            let onlyOngoing = false;
                            let showAll = false;

                            if (seriesIndex === 0) {         // ✅ Total (ahora es índice 0)
                                showAll = true;
                            } else if (seriesIndex === 1) {  // ✅ En Proceso (ahora es índice 1)
                                onlyOngoing = true;
                            } else if (seriesIndex === 2) {  // ✅ Contratados (ahora es índice 2)
                                onlyHired = true;
                            }

                            this.openRecruitmentList(stat.id, onlyHired, onlyOngoing, showAll);
                        }
                    }
                },
                plotOptions: {
                    bar: {
                        horizontal: true,
                        barHeight: '50%',  // ✅ Reducir altura para que se vean bien las 3 barras
                        distributed: false,
                        // ✅ IMPORTANTE: Configurar spacing entre grupos
                        dataLabels: {
                            position: 'center'
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function (val) {
                        return val > 0 ? val : '';
                    },
                    style: {
                        colors: ['#fff'],
                        fontSize: '11px',
                        fontWeight: 'bold'
                    }
                },
                stroke: {
                    width: 1,
                    colors: ['#fff']
                },
                title: {
                    text: this.props.title || 'Eficiencia de Contratación por Reclutador',
                    align: 'center',
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }
                },
                xaxis: {
                    categories: labels,
                    labels: {
                        show: false
                    }
                },
                yaxis: {
                    labels: {
                        show: true  // ✅ MANTENER: Mostrar nombres de reclutadores
                    }
                },
                legend: {
                    position: 'top',
                    horizontalAlign: 'left',
                    // ✅ OPCIONAL: Personalizar leyenda para distinguir mejor
                    markers: {
                        width: 12,
                        height: 12,
                        strokeWidth: 0,
                        strokeColor: '#fff',
                        fillColors: undefined,
                        radius: 12,
                        customHTML: undefined,
                        onClick: undefined,
                        offsetX: 0,
                        offsetY: 0
                    }
                },
                fill: {
                    opacity: [0.9, 1, 1]  // ✅ CORREGIR: Total menos opaco, otros sólidos
                },
                // ✅ NUEVA CONFIGURACIÓN: Para separar las barras visualmente
                grid: {
                    show: true,
                    borderColor: '#f1f1f1',
                    strokeDashArray: 0,
                    position: 'back',
                    xaxis: {
                        lines: {
                            show: true
                        }
                    },
                    yaxis: {
                        lines: {
                            show: false  // No mostrar líneas horizontales para mejor claridad
                        }
                    }
                },
                tooltip: {
                    shared: false,  // ✅ CAMBIAR: Tooltip individual por serie
                    intersect: true,
                    custom: function ({ series, seriesIndex, dataPointIndex, w }) {
                        const stat = recruiterStats[dataPointIndex];
                        const value = series[seriesIndex][dataPointIndex];

                        let content = '';
                        if (seriesIndex === 0) {
                            // ✅ Total - AZUL (ahora es índice 0)
                            content = `
                    <div class="px-3 py-2">
                        <div class="fw-bold">${stat.name}</div>
                        <div>Total Postulaciones: <span class="fw-bold text-primary">${value}</span></div>
                        <div class="text-muted">Total de candidatos gestionados</div>
                        <hr class="my-1">
                        <div class="small">En Proceso: ${stat.ongoing} | Contratados: ${stat.hired}</div>
                    </div>`;
                        } else if (seriesIndex === 1) {
                            // ✅ En Proceso - AMARILLO (ahora es índice 1)
                            content = `
                    <div class="px-3 py-2">
                        <div class="fw-bold">${stat.name}</div>
                        <div>En Proceso: <span class="fw-bold text-success">${value}</span></div>
                        <div class="text-muted">Candidatos actualmente en evaluación</div>
                    </div>`;
                        } else if (seriesIndex === 2) {
                            // ✅ Contratados - VERDE (ahora es índice 2)
                            content = `
                    <div class="px-3 py-2">
                        <div class="fw-bold">${stat.name}</div>
                        <div>Contratados: <span class="fw-bold text-warning">${value}</span></div>
                        <div class="text-muted">Tasa de conversión: ${stat.percentage}%</div>
                    </div>`;
                        }

                        return content;
                    }
                }
            }
        };

        // Forzar actualización
        this.state.chartData = { ...this.state.chartData };
    }

    // ✅ Métodos de filtrado por fechas - USAN this.props
    _addDateRangeToDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["create_date", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["create_date", "<=", this.props.endDate]);
        }
        return domain;
    }

    _getHiredDateRangeDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["date_closed", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["date_closed", "<=", this.props.endDate]);
        }
        return domain;
    }

    // ✅ Navegación a lista de postulaciones
    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false, showAll = false) {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);
        domain.push(["user_id", "=", userId]);

        // ✅ Filtrar por tipo de aplicación
        if (!showAll) {
            if (onlyHired) {
                domain.push(["application_status", "=", "hired"]);
            } else if (onlyOngoing) {
                domain.push(["application_status", "=", "ongoing"]);
            }
        }

        // ✅ Determinar nombre de la acción
        let actionName = 'Todas las Postulaciones';
        if (onlyHired) {
            actionName = 'Contratados';
        } else if (onlyOngoing) {
            actionName = 'En Proceso';
        }

        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: actionName,
            res_model: 'hr.applicant',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { active_test: false },
        });
    }
}