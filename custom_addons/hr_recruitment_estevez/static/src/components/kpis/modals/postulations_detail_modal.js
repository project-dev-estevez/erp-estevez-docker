/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class PostulationsDetailModal extends Component {

    static template = "hr_recruitment_estevez.PostulationsDetailModal";
    static components = { ChartRendererApex };
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
        actionService: { type: Object },
        onClose: { type: Function }
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = this.props.actionService;
        this.recruitmentStageService = useService("recruitment_stage");
        
        this.state = useState({
            chartConfig: null,
            isLoading: true,
            title: "Total de Postulaciones",
            stageData: []
        });

        onWillStart(async () => {
            await this.loadChartData();
        });
    }

    _addDateRangeToDomain(domain = []) {
        if (this.props.startDate) {
            // ✅ MEJOR: Usar formato de fecha simple YYYY-MM-DD
            domain.push(["create_date", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            // ✅ MEJOR: Usar <= con fecha final para incluir todo el día
            domain.push(["create_date", "<=", this.props.endDate]);
        }
        return domain;
    }

    get hasData() {
        return this.state.chartConfig && this.state.stageData.length > 0;
    }

    async loadChartData() {
        this.state.isLoading = true;

        try {
            // ✅ CAMBIO 1: Usar el servicio en lugar de consulta directa
            const stages = await this.recruitmentStageService.getStagesFromFirstContact();
            
            if (stages.length === 0) {
                console.error("❌ Modal: No se pudieron obtener las etapas");
                this.state.isLoading = false;
                return;
            }

            // 3. ✅ Contar candidatos por etapa CON FILTROS DE FECHA
            const stageData = [];
            const stageNames = [];
            const stageCounts = [];

            // 3.1 ✅ Contar candidatos ACTIVOS por etapa (igual que antes)
            for (const stage of stages) {
                let domain = [['stage_id', '=', stage.id]];
                domain = this._addDateRangeToDomain(domain);

                const count = await this.orm.searchCount("hr.applicant", domain);

                if (count > 0) {
                    stageData.push({
                        id: stage.id,
                        name: stage.name,
                        count: count,
                        sequence: stage.sequence,
                        type: 'active'
                    });
                    stageNames.push(stage.name);
                    stageCounts.push(count);
                }
            }

            // ✅ CAMBIO 2: Usar el servicio para candidatos rechazados
            const rejectedDomain = await this.recruitmentStageService.getRejectedDomainFromFirstContact(
                this._addDateRangeToDomain([])
            );

            const rejectedCount = await this.orm.searchCount(
                "hr.applicant", 
                rejectedDomain, 
                { context: { active_test: false } }
            );

            // 3.3 ✅ Agregar rechazados como etapa especial si hay candidatos (igual que antes)
            if (rejectedCount > 0) {
                stageData.push({
                    id: null,
                    name: 'Rechazados',
                    count: rejectedCount,
                    sequence: 999,
                    type: 'rejected'
                });
                stageNames.push('Rechazados');
                stageCounts.push(rejectedCount);
            }

            // 4. ✅ Actualizar título con información del rango (igual que antes)
            const totalCandidatos = stageCounts.reduce((a, b) => a + b, 0);
            const rangeText = this.getRangeText();
            this.state.title = `Total de Postulaciones${rangeText ? ` ${rangeText}` : ''}`;

            console.log(`📊 Modal: Total candidatos: ${totalCandidatos} (KPI debe coincidir)`);

            // 5. ✅ Guardar datos para navegación (igual que antes)
            this.state.stageData = stageData;

            // 6. ✅ Si no hay datos, mostrar mensaje (igual que antes)
            if (stageData.length === 0) {
                console.warn("⚠️ Modal: No hay candidatos en ninguna etapa para el rango seleccionado");
                this.state.chartConfig = null;
                this.state.isLoading = false;
                return;
            }

            // 7. ✅ Preparar configuración de la gráfica (igual que antes)
            this.state.chartConfig = {
                series: [{
                    name: 'Candidatos',
                    data: stageCounts
                }],
                categories: stageNames,
                colors: this.generateColorsWithRejected(stageNames.length, rejectedCount > 0),
                yAxisTitle: 'Número de Candidatos',
                options: {
                    chart: {
                        type: 'bar',
                        height: 400,
                        toolbar: {
                            show: false
                        },
                        events: {
                            dataPointSelection: (event, chartContext, config) => {
                                const dataPointIndex = config.dataPointIndex;
                                const stage = stageData[dataPointIndex];
                                this.openStageApplicants(stage);
                            }
                        }
                    },
                    title: {
                        text: `Distribución por Etapa (Total: ${totalCandidatos})`,
                        align: 'center',
                        style: {
                            fontSize: '18px',
                            fontWeight: 'bold',
                            color: '#263238'
                        }
                    },
                    plotOptions: {
                        bar: {
                            horizontal: false,
                            columnWidth: '70%',
                            borderRadius: 8,
                            dataLabels: {
                                position: 'top'
                            }
                        }
                    },
                    dataLabels: {
                        enabled: true,
                        formatter: function (val) {
                            return val;
                        },
                        style: {
                            fontSize: '12px',
                            fontWeight: 'bold',
                            colors: ['#fff']
                        }
                    },
                    colors: this.generateColorsWithRejected(stageNames.length, rejectedCount > 0),
                    xaxis: {
                        labels: {
                            show: true,
                            rotate: -45,
                            style: {
                                fontSize: '11px'
                            }
                        }
                    },
                    yaxis: {
                        labels: {
                            show: true
                        },
                        title: {
                            text: 'Candidatos'
                        }
                    },
                    tooltip: {
                        enabled: true,
                        y: {
                            formatter: function (val, opts) {
                                return val;
                            }
                        }
                    }
                }
            };

        } catch (error) {
            console.error("❌ Modal: Error cargando datos:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async openStageApplicants(stage) {
        try {
            let domain = [];
            let title = '';
            const rangeText = this.getRangeText();

            if (stage.type === 'rejected') {
                // ✅ CAMBIO 3: Usar el servicio en lugar de consulta directa
                domain = await this.recruitmentStageService.getRejectedDomainFromFirstContact([]);
                title = `❌ ${stage.name}${rangeText ? ` ${rangeText}` : ''} (${stage.count} candidatos)`;
            } else {
                domain = [['stage_id', '=', stage.id]];
                title = `📊 ${stage.name}${rangeText ? ` ${rangeText}` : ''} (${stage.count} candidatos)`;
            }

            domain = this._addDateRangeToDomain(domain);

            // ✅ Navegar usando actionService (igual que antes)
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: title,
                res_model: "hr.applicant",
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                target: "current",
                context: stage.type === 'rejected' ? 
                    { active_test: false } :
                    { default_stage_id: stage.id }
            });

            this.onCloseModal();

        } catch (error) {
            console.error("❌ Modal: Error en navegación:", error);
        }
    }

    getRangeText() {
        if (!this.props.startDate && !this.props.endDate) {
            return '';
        }

        return ` (${this.props.startDate} al ${this.props.endDate})`;
    }

    generateColors(count) {
        const colors = [
            '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB347',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#FF6B6B',
            '#AED6F1', '#A9DFBF', '#F9E79F', '#F8BBD0', '#DCEDC8', '#FFF9C4'
        ];
        return colors.slice(0, count);
    }

    generateColorsWithRejected(count, hasRejected) {
        const colors = [
            '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#FFB347',
            '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8C471', '#FF6B6B',
            '#AED6F1', '#A9DFBF', '#F9E79F', '#F8BBD0', '#DCEDC8', '#FFF9C4'
        ];
        
        let finalColors = colors.slice(0, count);
        
        // ✅ Si hay rechazados, el último color debe ser rojo
        if (hasRejected) {
            finalColors[finalColors.length - 1] = '#FF6B6B';  // Rojo para rechazados
        }
        
        return finalColors;
    }

    onCloseModal() {
        this.props.onClose();
    }
}