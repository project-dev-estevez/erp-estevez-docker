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

        // 6. Preparar datos para ApexCharts
        const labels = recruiterStats.map(r => r.name);
        const ongoingCounts = recruiterStats.map(r => r.ongoing);
        const hiredCounts = recruiterStats.map(r => r.hired);

        // 7. Configurar el gráfico
        this.state.chartData = {
            series: [
                {
                    name: 'En Proceso',
                    data: ongoingCounts
                },
                {
                    name: 'Contratados', 
                    data: hiredCounts
                }
            ],
            categories: labels,
            colors: ['#80c7fd', '#00E396'],
            meta: recruiterStats,
            filename: 'eficiencia_reclutadores',
            options: {
                chart: {
                    type: 'bar',
                    stacked: true,
                    height: this.props.height || 350,
                    events: {
                        dataPointSelection: (event, chartContext, config) => {
                            const seriesIndex = config.seriesIndex;
                            const dataPointIndex = config.dataPointIndex;
                            const stat = recruiterStats[dataPointIndex];

                            // Determinar filtro según serie
                            let onlyHired = false;
                            let onlyOngoing = false;
                            if (seriesIndex === 1) {
                                onlyHired = true;
                            } else if (seriesIndex === 0) {
                                onlyOngoing = true;
                            }

                            this.openRecruitmentList(stat.id, onlyHired, onlyOngoing);
                        }
                    }
                },
                plotOptions: {
                    bar: {
                        horizontal: true
                    }
                },
                dataLabels: {
                    enabled: true,
                    formatter: function (val) {
                        return val > 0 ? val : '';
                    },
                    style: {
                        colors: ['#fff'],
                        fontSize: '12px',
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
                        show: true
                    }
                },
                legend: {
                    position: 'top',
                    horizontalAlign: 'left'
                },
                fill: {
                    opacity: 1
                },
                tooltip: {
                    shared: true,
                    intersect: false,
                    custom: function ({ series, seriesIndex, dataPointIndex, w }) {
                        const stat = recruiterStats[dataPointIndex];
                        const ongoingValue = series[0][dataPointIndex];
                        const hiredValue = series[1][dataPointIndex];
                        const totalValue = ongoingValue + hiredValue;

                        return `
                        <div class="px-3 py-2">
                            <div class="fw-bold">${stat.name}</div>
                            <div>En Proceso: <span class="fw-bold text-primary">${ongoingValue}</span></div>
                            <div>Contratados: <span class="fw-bold text-success">${hiredValue}</span></div>
                            <div>Total: <span class="fw-bold">${totalValue}</span></div>
                            <div class="text-muted">Tasa de conversión: ${stat.percentage}%</div>
                        </div>
                    `;
                    }
                }
            }
        };

        // Forzar actualización
        this.state.chartData = { ...this.state.chartData };
        console.log("📊 RecruiterEfficiencyChart: Datos actualizados", this.state.chartData);
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
    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false) {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);
        domain.push(["user_id", "=", userId]);

        // Filtrar por tipo de aplicación
        if (onlyHired) {
            domain.push(["application_status", "=", "hired"]);
        } else if (onlyOngoing) {
            domain.push(["application_status", "=", "ongoing"]);
        }

        let actionName = 'Postulaciones';
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