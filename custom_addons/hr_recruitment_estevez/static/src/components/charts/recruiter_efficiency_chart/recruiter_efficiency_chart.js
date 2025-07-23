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
        onMounted: { type: Function, optional: true }
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

    async calculateRecruiterStats() {
        try {
            // ✅ PASO 1: Buscar la etapa "Primera Entrevista" (OBLIGATORIA)
            const primeraEntrevistaStage = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primera entrevista']],
                ['id', 'name', 'sequence'],
                { limit: 1 }
            );

            if (!primeraEntrevistaStage.length) {
                console.error("❌ RecruiterEfficiencyChart: Etapa 'Primera Entrevista' NO encontrada");
                // Usar datos vacíos si no se encuentra la etapa
                this.state.chartData = {
                    series: [],
                    categories: [],
                    colors: ['#FFD700', '#00E396', '#3f51b5'],
                    meta: [],
                    filename: 'eficiencia_reclutadores_post_primera_entrevista',
                    options: {}
                };
                return;
            }

            const primeraEntrevistaSequence = primeraEntrevistaStage[0].sequence;
            console.log("✅ RecruiterEfficiencyChart: Etapa 'Primera Entrevista' encontrada:", {
                id: primeraEntrevistaStage[0].id,
                name: primeraEntrevistaStage[0].name,
                sequence: primeraEntrevistaSequence
            });

            // ✅ PASO 2: Total postulaciones por reclutador que llegaron a Primera Entrevista
            let domain = [
                ['stage_id.sequence', '>=', primeraEntrevistaSequence],  // ✅ Al menos Primera Entrevista
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

            // ✅ PASO 3: Contratados por reclutador que llegaron a Primera Entrevista
            let hiredDomain = [
                ['stage_id.sequence', '>=', primeraEntrevistaSequence],  // ✅ Al menos Primera Entrevista
                ["application_status", "=", "hired"]
            ];
            hiredDomain = this._getHiredDateRangeDomain(hiredDomain);

            const hiredData = await this.orm.readGroup(
                "hr.applicant",
                hiredDomain,
                ["user_id"],
                ["user_id"]
            );

            // ✅ PASO 4: En proceso por reclutador que llegaron a Primera Entrevista
            let ongoingDomain = [
                ['stage_id.sequence', '>=', primeraEntrevistaSequence],  // ✅ Al menos Primera Entrevista
                ["application_status", "=", "ongoing"]
            ];
            ongoingDomain = this._addDateRangeToDomain(ongoingDomain);

            const ongoingData = await this.orm.readGroup(
                "hr.applicant",
                ongoingDomain,
                ["user_id"],
                ["user_id"]
            );

            // ✅ PASO 5: Debug de datos obtenidos
            console.log("📊 RecruiterEfficiencyChart datos post-Primera Entrevista:", {
                total: totalData.length,
                hired: hiredData.length,
                ongoing: ongoingData.length,
                primeraEntrevistaSequence
            });

            // ✅ PASO 6: Unir todos los conjuntos de usuarios
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

            // ✅ PASO 7: Construir el array final
            const recruiterStats = Object.values(recruiterMap).map(r => {
                const percentage = r.total > 0 ? ((r.hired / r.total) * 100).toFixed(2) : "0.00";
                return { ...r, percentage };
            });

            console.log("📊 RecruiterEfficiencyChart stats finales post-Primera Entrevista:", recruiterStats);

            // ✅ PASO 8: Preparar datos para el gráfico
            const labels = recruiterStats.map(r => r.name);
            const ongoingCounts = recruiterStats.map(r => r.ongoing);
            const hiredCounts = recruiterStats.map(r => r.hired);
            const totalCounts = recruiterStats.map(r => r.total);

            // ✅ PASO 9: CONFIGURAR gráfico
            this.state.chartData = {
                series: [
                    {
                        name: 'Total (Post-Primera Entrevista)',  // ✅ Título actualizado
                        data: totalCounts,
                        stack: 'total'
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
                colors: ['#FFD700', '#00E396', '#3f51b5'],
                meta: recruiterStats,
                filename: 'eficiencia_reclutadores_post_primera_entrevista',  // ✅ Nombre actualizado
                options: {
                    chart: {
                        type: 'bar',
                        stacked: true,
                        height: this.props.height || 400,
                        events: {
                            dataPointSelection: (event, chartContext, config) => {
                                const seriesIndex = config.seriesIndex;
                                const dataPointIndex = config.dataPointIndex;
                                const stat = recruiterStats[dataPointIndex];

                                let onlyHired = false;
                                let onlyOngoing = false;
                                let showAll = false;

                                if (seriesIndex === 0) {         // ✅ Total (índice 0)
                                    showAll = true;
                                } else if (seriesIndex === 1) {  // ✅ En Proceso (índice 1)
                                    onlyOngoing = true;
                                } else if (seriesIndex === 2) {  // ✅ Contratados (índice 2)
                                    onlyHired = true;
                                }

                                this.openRecruitmentList(stat.id, onlyHired, onlyOngoing, showAll);
                            }
                        }
                    },
                    plotOptions: {
                        bar: {
                            horizontal: true,
                            barHeight: '50%',
                            distributed: false,
                            dataLabels: {
                                position: 'center'
                            }
                        }
                    },
                    dataLabels: {
                        enabled: false,  // ✅ DESACTIVAR: Sin números en las barras 😄
                        // ✅ Código anterior comentado:
                        // formatter: function (val, opts) {
                        //     if (val > 5) {
                        //         return val;
                        //     }
                        //     return '';
                        // },
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
                        text: this.props.title || 'Eficiencia de Contratación por Reclutador (Post-Primera Entrevista)',  // ✅ Título actualizado
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
                            show: true
                        }
                    },
                    legend: {
                        position: 'top',
                        horizontalAlign: 'left',
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
                        opacity: [0.9, 1, 1]  // ✅ Total menos opaco, otros sólidos
                    },
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
                                show: false
                            }
                        }
                    },
                    tooltip: {
                        shared: false,
                        intersect: true,
                        custom: function ({ series, seriesIndex, dataPointIndex, w }) {
                            const stat = recruiterStats[dataPointIndex];
                            const value = series[seriesIndex][dataPointIndex];

                            let content = '';
                            if (seriesIndex === 0) {
                                // ✅ Total - DORADO
                                content = `
                        <div class="px-3 py-2">
                            <div class="fw-bold">${stat.name}</div>
                            <div>Total (Post-Primera Entrevista): <span class="fw-bold text-primary">${value}</span></div>
                            <div class="text-muted">Candidatos que llegaron al menos a Primera Entrevista</div>
                            <hr class="my-1">
                            <div class="small">En Proceso: ${stat.ongoing} | Contratados: ${stat.hired}</div>
                            <div class="small">Tasa de conversión: ${stat.percentage}%</div>
                        </div>`;
                            } else if (seriesIndex === 1) {
                                // ✅ En Proceso - VERDE
                                content = `
                        <div class="px-3 py-2">
                            <div class="fw-bold">${stat.name}</div>
                            <div>En Proceso: <span class="fw-bold text-success">${value}</span></div>
                            <div class="text-muted">Candidatos post-Primera Entrevista en evaluación</div>
                        </div>`;
                            } else if (seriesIndex === 2) {
                                // ✅ Contratados - AZUL
                                content = `
                        <div class="px-3 py-2">
                            <div class="fw-bold">${stat.name}</div>
                            <div>Contratados: <span class="fw-bold text-warning">${value}</span></div>
                            <div class="text-muted">Tasa de conversión post-Primera Entrevista: ${stat.percentage}%</div>
                        </div>`;
                            }

                            return content;
                        }
                    }
                }
            };

            // ✅ PASO 10: Forzar actualización
            this.state.chartData = { ...this.state.chartData };

        } catch (error) {
            console.error("❌ RecruiterEfficiencyChart: Error calculando stats:", error);
            this.state.chartData = {
                series: [],
                categories: [],
                colors: ['#FFD700', '#00E396', '#3f51b5'],
                meta: [],
                filename: 'eficiencia_reclutadores_post_primera_entrevista',
                options: {}
            };
        }
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