/** @odoo-module */

import { Component, useState, onWillStart, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex"; // ✅ CAMBIO: Usar ApexCharts

export class RecruitmentSourcesChart extends Component {
    static template = "hr_recruitment_estevez.RecruitmentSourcesChart";
    static components = { ChartRendererApex }; // ✅ CAMBIO: ApexCharts renderer
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

        this.state = useState({
            // ✅ NUEVO: Configuración para ApexCharts
            apexConfig: {
                series: [],
                categories: [],
                options: {}
            },
            indicatorsSourceRecruitment: { sources: [] },
            isLoading: true,
            hasData: false,
            // ✅ NUEVO: Datos internos para manejo
            sourcesData: [],
            chartKey: 'chart-' + Date.now()
        });

        onWillStart(async () => {
            await this.loadChart();
        });

        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });

        // ✅ NUEVO: Detectar cambios en props (fechas)
        onWillUpdateProps(async (nextProps) => {
            if (this.props.startDate !== nextProps.startDate || 
                this.props.endDate !== nextProps.endDate) {
                
                console.log("📅 RecruitmentSourcesChart: Fechas cambiaron, recargando...");
                
                // Actualizar props temporalmente
                this.tempProps = nextProps;
                await this.loadChart();
                this.tempProps = null;
            }
        });
    }

    // ✅ NUEVO: Método para obtener props actuales
    getCurrentProps() {
        return this.tempProps || this.props;
    }

    async loadChart() {
        const currentProps = this.getCurrentProps();
        
        console.log("📊 RecruitmentSourcesChart: Cargando datos...", {
            startDate: currentProps.startDate,
            endDate: currentProps.endDate
        });

        this.state.isLoading = true;

        try {
            // ✅ MANTENER: Lógica secuencial original
            await this.getSourceRecruitment();
            await this.getIndicatorsSourceRecruitment();
            
            console.log("✅ RecruitmentSourcesChart: Datos cargados correctamente");
        } catch (error) {
            console.error("❌ RecruitmentSourcesChart: Error cargando datos:", error);
            this.showEmptyChart();
        } finally {
            this.state.isLoading = false;
        }
    }

    // ✅ REFINADO: Método principal optimizado para ApexCharts
    async getSourceRecruitment() {
        // 1. Total postulaciones por fuente (por create_date)
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);

        const totalData = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["source_id"],
            ["source_id"]
        );

        // 2. Contratados por fuente (por date_closed)
        let hiredDomain = [
            ["application_status", "=", "hired"]
        ];
        hiredDomain = this._getHiredDateRangeDomain(hiredDomain);

        const hiredData = await this.orm.readGroup(
            "hr.applicant",
            hiredDomain,
            ["source_id"],
            ["source_id"]
        );

        // 3. Unir ambos conjuntos de fuentes
        const sourceMap = {};

        // Total postulaciones
        for (const r of totalData) {
            const id = (r.source_id && r.source_id[0]) || false;
            const label = (r.source_id && r.source_id[1]) || "Sin fuente";
            sourceMap[id] = {
                sourceId: id,
                label,
                total: r.source_id_count,
                hired: 0
            };
        }

        // Contratados
        for (const r of hiredData) {
            const id = (r.source_id && r.source_id[0]) || false;
            const label = (r.source_id && r.source_id[1]) || "Sin fuente";
            if (!sourceMap[id]) {
                sourceMap[id] = { sourceId: id, label, total: 0, hired: 0 };
            }
            sourceMap[id].hired = r.source_id_count;
        }

        // 4. Preparar datos
        const sourcesData = Object.values(sourceMap);
        
        console.log("📈 RecruitmentSourcesChart: Fuentes procesadas:", sourcesData.length);

        if (sourcesData.length === 0) {
            console.log("⚠️ RecruitmentSourcesChart: No hay fuentes de reclutamiento");
            this.showEmptyChart();
            return;
        }

        this.state.hasData = true;
        this.state.sourcesData = sourcesData;

        // ✅ PREPARAR datos para ApexCharts
        const labels = sourcesData.map(s => s.label);
        const series = sourcesData.map(s => s.total);
        const colors = this.getPolarAreaColors(labels.length);
        this.state.chartKey = 'chart-' + Date.now();

        console.log("🏷️ RecruitmentSourcesChart: Labels generados:", labels);
        console.log("📊 RecruitmentSourcesChart: Series generadas:", series);

        // ✅ CONFIGURAR APEXCHARTS CON ACTUALIZACIÓN COMPLETA
        this.state.apexConfig = {
            series: series,
            // ✅ IMPORTANTE: Asegurar que categories y labels estén sincronizados
            categories: labels,
            options: {
                title: {
                    text: this.props.title || 'Efectividad de las Fuentes de Reclutamiento',
                    align: 'center',
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }
                },
                chart: {
                    type: 'pie',
                    height: this.props.height || 400,
                    // ✅ AGREGAR: ID único para forzar recreación
                    id: 'recruitment-sources-chart-' + Date.now(),
                    events: {
                        dataPointSelection: (event, chartContext, config) => {
                            const sourceData = this.state.sourcesData[config.dataPointIndex];
                            this.openSourceRecruitmentList(sourceData.sourceId);
                        }
                    }
                },
                // ✅ CRÍTICO: Labels debe estar aquí también
                labels: labels,
                colors: colors,
                stroke: {
                    colors: ['#fff'],
                    width: 2
                },
                fill: {
                    opacity: 0.8
                },
                plotOptions: {
                    polarArea: {
                        rings: {
                            strokeWidth: 1,
                            strokeColor: '#e8e8e8'
                        },
                        spokes: {
                            strokeWidth: 1,
                            connectorColors: '#e8e8e8'
                        }
                    }
                },
                dataLabels: {
                    enabled: false,
                    formatter: function(val) {
                        return Math.round(val);
                    },
                    style: {
                        fontSize: '12px',
                        fontWeight: 'bold',
                        colors: ['#fff']
                    }
                },
                legend: {
                    position: 'bottom',
                    horizontalAlign: 'center',
                    floating: false,
                    fontSize: '12px',
                    itemMargin: {
                        horizontal: 10,
                        vertical: 5
                    }
                },
                tooltip: {
                    y: {
                        formatter: function (value) {
                            return value + ' postulaciones';
                        }
                    }
                },
                responsive: [{
                    breakpoint: 480,
                    options: {
                        chart: {
                            height: 300
                        },
                        legend: {
                            position: 'bottom'
                        }
                    }
                }]
            }
        };

        console.log("✅ RecruitmentSourcesChart: Configuración ApexCharts preparada con labels:", labels);
    }

    // ✅ OPTIMIZADO: Método de indicadores usando datos ya procesados
    async getIndicatorsSourceRecruitment() {
        // Usar los datos que ya calculamos en getSourceRecruitment
        if (!this.state.sourcesData || this.state.sourcesData.length === 0) {
            this.state.indicatorsSourceRecruitment = { sources: [] };
            return;
        }

        // Construir indicadores con porcentajes
        let indicators = this.state.sourcesData.map(r => {
            const percentage = r.total > 0 ? ((r.hired / r.total) * 100).toFixed(2) : "0.00";
            return { 
                id: r.sourceId,
                label: r.label, 
                total: r.total,
                hired: r.hired,
                percentage 
            };
        });

        // Filtrar solo los que tengan al menos 1 contratado
        indicators = indicators.filter(ind => ind.hired > 0);

        // Ordenar por efectividad (porcentaje de contratación)
        indicators.sort((a, b) => parseFloat(b.percentage) - parseFloat(a.percentage));

        this.state.indicatorsSourceRecruitment.sources = indicators;

        console.log("✅ RecruitmentSourcesChart: Indicadores calculados:", indicators.length);
    }

    // ✅ MANTENER: Método de navegación original
    async openSourceRecruitmentList(sourceId) {
        const currentProps = this.getCurrentProps();
        let domain = [];
        
        if (currentProps.startDate) {
            domain.push(["create_date", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["create_date", "<=", currentProps.endDate]);
        }
    
        // Filtra por source_id
        if (sourceId) {
            domain.push(["source_id", "=", sourceId]);
        } else {
            domain.push(["source_id", "=", false]);
        }
    
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Postulaciones por Fuente',
            res_model: 'hr.applicant',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { active_test: false },
        });
    }

    // ✅ REFINADO: Gráfico vacío para ApexCharts (forzar limpieza)
    showEmptyChart() {
        this.state.hasData = false;
        this.state.chartKey = 'empty-' + Date.now();
        // ✅ LIMPIAR completamente la configuración
        this.state.apexConfig = {
            series: [],
            categories: [],
            options: {
                labels: [],
                chart: {
                    // ✅ ID único para forzar recreación
                    id: 'empty-chart-' + Date.now()
                }
            }
        };
        this.state.indicatorsSourceRecruitment = { sources: [] };
        this.state.sourcesData = [];
    }

    // ✅ MANTENER: Helper para clasificar porcentajes
    getPercentageClass(percentage) {
        const perc = parseFloat(percentage);
        if (perc >= 20) return 'text-success';
        if (perc >= 10) return 'text-warning';
        return 'text-danger';
    }

    // ✅ MANTENER: Métodos de filtrado por fechas
    _addDateRangeToDomain(domain = []) {
        const currentProps = this.getCurrentProps();
        
        if (currentProps.startDate) {
            domain.push(["create_date", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["create_date", "<=", currentProps.endDate]);
        }
        return domain;
    }

    _getHiredDateRangeDomain(domain = []) {
        const currentProps = this.getCurrentProps();
        
        if (currentProps.startDate) {
            domain.push(["date_closed", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["date_closed", "<=", currentProps.endDate]);
        }
        return domain;
    }

    getPolarAreaColors(count) {
        // Paleta extendida, tonos dorados, verdes y azules, sin repetir
        const palette = [
            '#FFD700', // Dorado
            '#00E396', // Verde vibrante
            '#3f51b5', // Azul vibrante
            '#FF6F61', // Coral premium
            '#2EC4B6', // Turquesa premium
            '#FFB400', // Amarillo premium
            '#5F4B8B', // Púrpura premium
            '#009688', // Verde azulado
            '#F95D6A', // Rojo coral
            '#4ECDC4', // Verde pastel
            '#5567FF', // Azul eléctrico
            '#FFB7B2', // Rosa pastel
            '#6A4C93', // Púrpura oscuro
            '#43AA8B', // Verde suave
            '#FFD6E0', // Rosa claro
            '#B2B1CF', // Lavanda premium
            '#FFAB00', // Amarillo intenso
            '#2D9CDB', // Azul claro premium
            '#9C27B0', // Morado vibrante
            '#00BFAE', // Verde agua premium
        ];

        // Si hay más fuentes que colores, genera tonos derivados (sin repetir)
        if (count <= palette.length) {
            return palette.slice(0, count);
        }
        const colors = [...palette];
        for (let i = palette.length; i < count; i++) {
            // Genera tonos derivados usando HSL, manteniendo la gama
            const hue = 45 + (i * 25) % 360; // Entre dorado y azul
            const saturation = 80;
            const lightness = 55;
            colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }
        return colors;
    }

    // ✅ REFINADO: Método de refresh optimizado
    async refresh() {
        console.log("🔄 RecruitmentSourcesChart: Iniciando refresh...");
        
        // ✅ LIMPIAR estado antes de recargar
        this.showEmptyChart();
        
        // ✅ Pequeña pausa para asegurar limpieza
        await new Promise(resolve => setTimeout(resolve, 100));
        
        await this.loadChart();
        console.log("✅ RecruitmentSourcesChart: Refresh completado");
    }
}