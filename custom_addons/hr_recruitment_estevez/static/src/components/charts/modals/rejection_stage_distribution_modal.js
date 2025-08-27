/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class RejectionStageDistributionModal extends Component {
    static template = "hr_recruitment_estevez.RejectionStageDistributionModal";
    static components = { ChartRendererApex };
    static props = {
        refuseReasonId: { type: Number },
        refuseReasonName: { type: String },
        isCandidateDecline: { type: Boolean },
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true },
        onClose: { type: Function }
    };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            isLoading: true,
            chartConfig: null,
            title: "",
            stageData: [],
            stages: [],
        });

        onWillStart(async () => {
            await this.loadStageDistribution();
        });
    }

    get hasData() {
        return this.state.chartConfig && this.state.stageData.length > 0;
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

    async loadStageDistribution() {
        this.state.isLoading = true;
        try {
            // 1. Buscar secuencia de "Primer contacto"
            const primerContactoStage = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['name', 'ilike', 'primer contacto']],
                ['sequence'],
                { limit: 1 }
            );
            if (!primerContactoStage.length) {
                this.state.isLoading = false;
                return;
            }
            const primerContactoSequence = primerContactoStage[0].sequence;

            // 2. Buscar todas las etapas >= primer contacto
            const stages = await this.orm.searchRead(
                'hr.recruitment.stage',
                [['sequence', '>=', primerContactoSequence]],
                ['id', 'name', 'sequence'],
                { order: 'sequence asc' }
            );

            // 3. Primero obtener el total de candidatos con este motivo de rechazo
            // usando el mismo dominio que la gráfica principal
            let baseDomain = [
                ['application_status', '=', 'refused'],
                ['refuse_reason_id', '=', this.props.refuseReasonId],
                ['stage_id.sequence', '>=', primerContactoSequence]
            ];
            baseDomain = this._addDateRangeToDomain(baseDomain);

            const totalCount = await this.orm.searchCount("hr.applicant", baseDomain, { context: { active_test: false } });
            console.log(`📊 Total esperado para "${this.props.refuseReasonName}": ${totalCount}`);

            // 4. Contar candidatos rechazados/declinados por etapa y motivo
            this.state.stages = stages;
            const stageNames = [];
            const stageCounts = [];
            const stageData = [];
            let totalModalCount = 0;

            for (const stage of stages) {
                let domain = [
                    ['stage_id', '=', stage.id],
                    ['refuse_reason_id', '=', this.props.refuseReasonId],
                    ['application_status', '=', 'refused']
                ];
                domain = this._addDateRangeToDomain(domain);
                
                const count = await this.orm.searchCount("hr.applicant", domain, { context: { active_test: false } });
                if (count > 0) {
                    stageNames.push(stage.name);
                    stageCounts.push(count);
                    stageData.push({ name: stage.name, count, id: stage.id });
                    totalModalCount += count;
                    console.log(`📈 Etapa "${stage.name}": ${count} candidatos`);
                }
            }

            console.log(`📊 Total en modal: ${totalModalCount}, Total esperado: ${totalCount}`);

            this.state.stageData = stageData;
            this.state.title = `Distribución por etapa: ${this.props.refuseReasonName} (Total: ${totalModalCount})`;

            if (stageData.length === 0) {
                this.state.chartConfig = null;
            } else {
                this.state.chartConfig = {
                    series: [{ name: "Candidatos", data: stageCounts }],
                    options: {
                        chart: {
                            type: "bar",
                            height: 350,
                            events: {
                                dataPointSelection: (event, chartContext, config) => {
                                    const stageIndex = config.dataPointIndex;
                                    // Usa el id real de la etapa desde stageData
                                    const stageId = this.state.stageData[stageIndex].id;
                                    const stageName = this.state.stageData[stageIndex].name;
                                    this.openApplicantsByJob({ id: stageId, name: stageName });
                                }
                            }
                        },
                        xaxis: { categories: stageNames },
                        yaxis: { title: { text: "Candidatos" } },
                        dataLabels: { enabled: true },
                        title: {
                            text: `Etapas donde se presentó "${this.props.refuseReasonName}"`,
                            align: "center"
                        }
                    }
                };
            }
        } catch (error) {
            console.error("❌ Error cargando distribución por etapa:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async openApplicantsByJob(stage) {
        let domain = [
            ['stage_id', '=', stage.id],
            ['refuse_reason_id', '=', this.props.refuseReasonId],
            ['application_status', '=', 'refused'],
            ['active', 'in', [true, false]],
        ];
        if (this.props.startDate) {
            domain.push(["create_date", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["create_date", "<=", this.props.endDate]);
        }

        console.log("Dominio enviado a la acción:", JSON.stringify(domain, null, 2));
        console.log("stage.id:", stage.id, "stage.name:", stage.name, "refuseReasonId:", this.props.refuseReasonId);

        await this.actionService.doAction({
            type: "ir.actions.act_window",
            name: `Candidatos rechazados en "${stage.name}"`,
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: {
                search_default_group_by_job: 1,
                active_test: false
            }
        });
    }

    onCloseModal() {
        this.props.onClose();
    }
}