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
        onClose: { type: Function }
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            isLoading: true,
            chartConfig: null,
            title: "",
            stageData: []
        });

        onWillStart(async () => {
            await this.loadStageDistribution();
        });
    }

    get hasData() {
        return this.state.chartConfig && this.state.stageData.length > 0;
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

            // 3. Contar candidatos rechazados/declinados por etapa y motivo
            const stageNames = [];
            const stageCounts = [];
            const stageData = [];

            for (const stage of stages) {
                let domain = [
                    ['stage_id', '=', stage.id],
                    ['refuse_reason_id', '=', this.props.refuseReasonId],
                    ['application_status', '=', 'refused']
                ];
                const count = await this.orm.searchCount("hr.applicant", domain);
                if (count > 0) {
                    stageNames.push(stage.name);
                    stageCounts.push(count);
                    stageData.push({ name: stage.name, count });
                }
            }

            this.state.stageData = stageData;
            this.state.title = `Distribución por etapa: ${this.props.refuseReasonName}`;

            if (stageData.length === 0) {
                this.state.chartConfig = null;
            } else {
                this.state.chartConfig = {
                    series: [{ name: "Candidatos", data: stageCounts }],
                    categories: stageNames,
                    yAxisTitle: "Número de Candidatos"
                };
            }
        } catch (error) {
            console.error("❌ Error cargando distribución por etapa:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    onCloseModal() {
        this.props.onClose();
    }
}