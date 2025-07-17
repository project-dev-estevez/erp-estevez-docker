/** @odoo-module */

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRenderer } from "../../chart_renderer/chart_renderer";

export class RecruitmentSourcesChart extends Component {
    static template = "hr_recruitment_estevez.RecruitmentSourcesChart";
    static components = { ChartRenderer };
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
            sourceRecruitment: {
                data: { labels: [], datasets: [] },
                options: {},
                meta: []
            },
            indicatorsSourceRecruitment: { sources: [] },
            isLoading: true,
            hasData: false
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
        console.log("📊 RecruitmentSourcesChart: Cargando datos...", {
            startDate: this.props.startDate,
            endDate: this.props.endDate
        });

        this.state.isLoading = true;

        try {
            // ✅ USAR LA LÓGICA ORIGINAL: Secuencial
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

    // ✅ MÉTODO PRINCIPAL: Lógica EXACTA del dashboard original
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
                hired: 0 // se llenará después
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

        // 4. Construir arrays para la gráfica
        const sourcesData = Object.values(sourceMap);
        const labels = sourcesData.map(s => s.label);
        const totalCounts = sourcesData.map(s => s.total);
        const hiredCounts = sourcesData.map(s => s.hired);
        const colors = this.getPastelColors(labels.length);

        console.log("📈 RecruitmentSourcesChart: Fuentes procesadas:", sourcesData.length);

        if (sourcesData.length === 0) {
            console.log("⚠️ RecruitmentSourcesChart: No hay fuentes de reclutamiento");
            this.showEmptyChart();
            return;
        }

        this.state.hasData = true;

        this.state.sourceRecruitment = {
            data: {
                labels,
                datasets: [
                    {
                        label: "Total Postulaciones",
                        data: totalCounts,
                        backgroundColor: colors,
                    },
                    {
                        label: "Contratados",
                        data: hiredCounts,
                        backgroundColor: "hsl(140,70%,85%)"
                    }
                ]
            },
            meta: sourcesData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, activeElements) => {
                    if (!activeElements.length) return;
                    const { index } = activeElements[0];
                    const src = this.state.sourceRecruitment.meta[index];
                    this.openSourceRecruitmentList(src.sourceId);
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const src = sourcesData[ctx.dataIndex];
                                const datasetLabel = ctx.dataset.label;
                                const value = ctx.dataset.data[ctx.dataIndex];
                                return `${datasetLabel} - ${src.label}: ${value}`;
                            }
                        }
                    }
                }
            }
        };
        
        // Forzar refresco
        this.state.sourceRecruitment = { ...this.state.sourceRecruitment };

        console.log("✅ RecruitmentSourcesChart: Gráfico configurado");
    }

    // ✅ MÉTODO SECUNDARIO: Lógica EXACTA del dashboard original
    async getIndicatorsSourceRecruitment() {
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
                id,
                label,
                total: r.source_id_count,
                hired: 0 // se llenará después
            };
        }

        // Contratados
        for (const r of hiredData) {
            const id = (r.source_id && r.source_id[0]) || false;
            const label = (r.source_id && r.source_id[1]) || "Sin fuente";
            if (!sourceMap[id]) {
                sourceMap[id] = { id, label, total: 0, hired: 0 };
            }
            sourceMap[id].hired = r.source_id_count;
        }

        // 4. Construir el array de indicadores
        const indicators = Object.values(sourceMap).map(r => {
            const percentage = r.total > 0 ? ((r.hired / r.total) * 100).toFixed(2) : "0.00";
            return { ...r, percentage };
        });

        // 5. Guarda en el estado
        this.state.indicatorsSourceRecruitment.sources = indicators;

        console.log("✅ RecruitmentSourcesChart: Indicadores calculados:", indicators.length);
    }

    // ✅ MÉTODO: Abrir lista de fuentes (igual que en dashboard)
    async openSourceRecruitmentList(sourceId) {
        let domain = [];
        domain = this._addDateRangeToDomain(domain);
    
        // Filtra por source_id
        if (sourceId) {
            domain.push(["source_id", "=", sourceId]);
        } else {
            // opcional: mostrar también los sin fuente
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

    // ✅ MÉTODO: Mostrar gráfico vacío
    showEmptyChart() {
        this.state.hasData = false;
        this.state.sourceRecruitment = {
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            },
            meta: []
        };
        this.state.indicatorsSourceRecruitment = { sources: [] };
    }

    // ✅ NUEVO: Función helper para clasificar porcentajes
    getPercentageClass(percentage) {
        const perc = parseFloat(percentage);
        if (perc >= 20) return 'text-success';
        if (perc >= 10) return 'text-warning';
        return 'text-danger';
    }

    // ✅ MÉTODOS DE FILTRADO POR FECHAS
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

    // ✅ MÉTODO: Generar colores pastel
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

    // ✅ MÉTODO PÚBLICO: Recargar datos
    async refresh() {
        console.log("🔄 RecruitmentSourcesChart: Iniciando refresh...");
        
        // Mostrar loading
        this.state.isLoading = true;
        
        try {
            // Cargar nuevos datos
            await this.loadChart();
            
            // ✅ TRUCO: Forzar re-render completo
            this.state.sourceRecruitment = { 
                ...this.state.sourceRecruitment,
                _forceUpdate: Date.now() // Timestamp para forzar cambio
            };
            
            this.state.indicatorsSourceRecruitment = { 
                ...this.state.indicatorsSourceRecruitment,
                _forceUpdate: Date.now()
            };
            
            console.log("✅ RecruitmentSourcesChart: Refresh completado");
        } catch (error) {
            console.error("❌ RecruitmentSourcesChart: Error en refresh:", error);
        }
    }
}