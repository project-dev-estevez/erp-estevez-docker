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
            // ✅ CAMBIO: Agregar 1 día a la fecha de inicio
            const startDate = new Date(this.props.startDate);
            startDate.setDate(startDate.getDate() + 1);
            const adjustedStartDate = startDate.toISOString().split('T')[0];  // Formato YYYY-MM-DD
            domain.push(["create_date", ">=", adjustedStartDate]);
        }
        if (this.props.endDate) {
            // ✅ CAMBIO: Agregar 1 día a la fecha de fin
            const endDate = new Date(this.props.endDate);
            endDate.setDate(endDate.getDate() + 1);
            const adjustedEndDate = endDate.toISOString().split('T')[0];  // Formato YYYY-MM-DD
            domain.push(["create_date", "<=", adjustedEndDate]);
        }
        return domain;
    }

    get hasData() {
        return this.state.chartConfig && this.state.stageData.length > 0;
    }

    async loadChartData() {
        this.state.isLoading = true;

        try {
            // 1. ✅ Buscar etapa "Primer contacto"
            const primerContactoStage = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primer contacto']],
                ['id', 'name', 'sequence'],
                { limit: 1 }
            );

            if (!primerContactoStage.length) {
                console.error("❌ Modal: Etapa 'Primer contacto' no encontrada");
                this.state.isLoading = false;
                return;
            }

            const primerContactoSequence = primerContactoStage[0].sequence;

            // 2. ✅ Obtener todas las etapas después de primer contacto
            const stages = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['sequence', '>', primerContactoSequence]],
                ['id', 'name', 'sequence'],
                { order: 'sequence asc' }
            );

            // 3. ✅ Contar candidatos por etapa CON FILTROS DE FECHA
            const stageData = [];
            const stageNames = [];
            const stageCounts = [];

            // 3.1 ✅ Contar candidatos ACTIVOS por etapa
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
                        type: 'active'  // ✅ Marcar como activo
                    });
                    stageNames.push(stage.name);
                    stageCounts.push(count);
                }
            }

            // 3.2 ✅ NUEVO: Contar candidatos RECHAZADOS que superaron primer contacto
            let rejectedDomain = [
                ['stage_id.sequence', '>', primerContactoSequence],
                ['application_status', '=', 'refused']  // ✅ Solo rechazados
            ];
            rejectedDomain = this._addDateRangeToDomain(rejectedDomain);

            const rejectedCount = await this.orm.searchCount(
                "hr.applicant", 
                rejectedDomain, 
                { context: { active_test: false } }  // ✅ Incluir inactivos
            );

            // 3.3 ✅ Agregar rechazados como etapa especial si hay candidatos
            if (rejectedCount > 0) {
                stageData.push({
                    id: null,  // No tiene etapa específica
                    name: 'Rechazados',
                    count: rejectedCount,
                    sequence: 999,  // Al final
                    type: 'rejected'  // ✅ Marcar como rechazado
                });
                stageNames.push('Rechazados');
                stageCounts.push(rejectedCount);
            }

            // 4. ✅ Actualizar título con información del rango
            const totalCandidatos = stageCounts.reduce((a, b) => a + b, 0);
            const rangeText = this.getRangeText();
            this.state.title = `Total de Postulaciones${rangeText ? ` ${rangeText}` : ''}`;

            console.log(`📊 Modal: Total candidatos: ${totalCandidatos} (KPI debe coincidir)`);

            // 5. ✅ Guardar datos para navegación
            this.state.stageData = stageData;

            // 6. ✅ Si no hay datos, mostrar mensaje
            if (stageData.length === 0) {
                console.warn("⚠️ Modal: No hay candidatos en ninguna etapa para el rango seleccionado");
                this.state.chartConfig = null;
                this.state.isLoading = false;
                return;
            }

            // 7. ✅ Preparar configuración de la gráfica con colores especiales
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
                    // ...resto de configuración igual...
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
                                const stageName = stageNames[opts.dataPointIndex];
                                return `${val} candidato${val !== 1 ? 's' : ''} en ${stageName}`;
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
                // ✅ Dominio especial para rechazados
                const primerContactoStage = await this.orm.searchRead(
                    'hr.recruitment.stage',
                    [['name', 'ilike', 'primer contacto']],
                    ['sequence'],
                    { limit: 1 }
                );
                
                if (primerContactoStage.length > 0) {
                    const sequence = primerContactoStage[0].sequence;
                    domain = [
                        ['stage_id.sequence', '>', sequence],
                        ['application_status', '=', 'refused']
                    ];
                } else {
                    domain = [['application_status', '=', 'refused']];
                }
                
                title = `❌ ${stage.name}${rangeText ? ` ${rangeText}` : ''} (${stage.count} candidatos)`;
            } else {
                // ✅ Dominio normal para etapas activas
                domain = [['stage_id', '=', stage.id]];
                title = `📊 ${stage.name}${rangeText ? ` ${rangeText}` : ''} (${stage.count} candidatos)`;
            }

            domain = this._addDateRangeToDomain(domain);

            // ✅ Navegar usando actionService
            await this.actionService.doAction({
                type: "ir.actions.act_window",
                name: title,
                res_model: "hr.applicant",
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                target: "current",
                context: stage.type === 'rejected' ? 
                    { active_test: false } :  // ✅ Para rechazados, incluir inactivos
                    { default_stage_id: stage.id }
            });

            this.onCloseModal();

        } catch (error) {
            console.error("❌ Modal: Error en navegación:", error);
        }
    }

    getRangeText() {
        if (this.props.startDate && this.props.endDate) {
            // ✅ Ajustar fecha de inicio sumando 1 día
            const startDate = new Date(this.props.startDate);
            startDate.setDate(startDate.getDate() + 1);
            const start = startDate.toLocaleDateString('es-ES');
            
            // ✅ Ajustar fecha de fin sumando 1 día
            const endDate = new Date(this.props.endDate);
            endDate.setDate(endDate.getDate() + 1);
            const end = endDate.toLocaleDateString('es-ES');
            
            return `(${start} - ${end})`;
        } else if (this.props.startDate) {
            // ✅ Ajustar fecha de inicio sumando 1 día
            const startDate = new Date(this.props.startDate);
            startDate.setDate(startDate.getDate() + 1);
            const start = startDate.toLocaleDateString('es-ES');
            return `(desde ${start})`;
        } else if (this.props.endDate) {
            // ✅ Ajustar fecha de fin sumando 1 día
            const endDate = new Date(this.props.endDate);
            endDate.setDate(endDate.getDate() + 1);
            const end = endDate.toLocaleDateString('es-ES');
            return `(hasta ${end})`;
        }
        return '';
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