/** @odoo-module */

import { Component, useState, onWillStart, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex"; // ✅ APEX CHARTS!

export class RecruitmentFunnelChart extends Component {
    static template = "hr_recruitment_estevez.RecruitmentFunnelChart";
    static components = { ChartRendererApex }; // ✅ APEX CHARTS!
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
        this.recruitmentStageService = useService("recruitment_stage"); 

        this.state = useState({
            // 🔍 Selector de vacante
            selectedVacancy: false,
            availableVacancies: [],
            vacancyOptions: [],
            filteredVacancyOptions: [],
            vacancySearchText: "Todas Las Vacantes",
            isVacancyDropdownOpen: false,
            
            // 📊 Métricas de vacante
            vacancyMetrics: {
                status: 'Global',
                openDuration: '',
                openDate: '',
                applicants: 0,
                hired: 0,
                hiredFromPrevious: 0,
                refused: 0,
                topRefuseReason: '',
                requestedPositions: 0
            },
            
            // 🎪 Datos del embudo
            funnelRecruitment: {},
            apexConfig: {
                series: [],
                options: {}
            }, // ✅ CONFIGURACIÓN APEX
            chartKey: 'funnel-chart-' + Date.now(), // ✅ PARA FORZAR RE-RENDER
            
            // 🔄 Estados
            isLoading: true,
            hasData: false
        });

        onWillStart(async () => {
            await this.loadFunnelData();
        });

        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });

        onWillUpdateProps(async (nextProps) => {
            if (this.props.startDate !== nextProps.startDate || 
                this.props.endDate !== nextProps.endDate) {
                
                console.log("📅 RecruitmentFunnelChart: Fechas cambiaron, recargando...");
                
                this.tempProps = nextProps;
                await this.loadFunnelData();
                this.tempProps = null;
            }
        });
    }

    getCurrentProps() {
        return this.tempProps || this.props;
    }

    async loadFunnelData() {
        this.state.isLoading = true;

        try {
            await Promise.all([
                this.getAllVacancies(),
                this.getVacancyMetrics(),
                this.getFunnelRecruitment()
            ]);
        } catch (error) {
            console.error("❌ RecruitmentFunnelChart: Error cargando datos:", error);
            this.showEmptyChart();
        } finally {
            this.state.isLoading = false;
        }
    }

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

    _addPublishDateRangeToDomain(domain = []) {
        const currentProps = this.getCurrentProps();
        
        if (currentProps.startDate) {
            domain.push(["publish_date", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["publish_date", "<=", currentProps.endDate]);
        }
        return domain;
    }

    _getHiredInRangeDomain(domain = []) {
        const currentProps = this.getCurrentProps();
        
        // ✅ Filtro 1: Se crearon en el rango (create_date)
        if (currentProps.startDate) {
            domain.push(["create_date", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["create_date", "<=", currentProps.endDate]);
        }
        
        // ✅ Filtro 2: Se contrataron en el rango (date_closed)
        if (currentProps.startDate) {
            domain.push(["date_closed", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["date_closed", "<=", currentProps.endDate]);
        }
        
        return domain;
    }

    _getHiredFromPreviousPeriodDomain(domain = []) {
        const currentProps = this.getCurrentProps();
        
        // ✅ Filtro 1: Se crearon ANTES del rango (create_date < startDate)
        if (currentProps.startDate) {
            domain.push(["create_date", "<", currentProps.startDate]);
        }
        
        // ✅ Filtro 2: Se contrataron DENTRO del rango (date_closed >= startDate && <= endDate)
        if (currentProps.startDate) {
            domain.push(["date_closed", ">=", currentProps.startDate]);
        }
        if (currentProps.endDate) {
            domain.push(["date_closed", "<=", currentProps.endDate]);
        }
        
        return domain;
    }

    // ✅ NUEVA función para calcular hired count de período anterior (global)
    async _calculateGlobalHiredFromPreviousPeriod() {
        let hiredDomain = [
            ['application_status', '=', 'hired']
        ];
        hiredDomain = this._getHiredFromPreviousPeriodDomain(hiredDomain);
        return await this.orm.searchCount('hr.applicant', hiredDomain);
    }

    // ✅ NUEVA función para calcular hired count de período anterior (específico)
    async _calculateHiredFromPreviousPeriod(jobId) {
        let hiredDomain = [
            ['job_id', '=', jobId],
            ['application_status', '=', 'hired']
        ];
        hiredDomain = this._getHiredFromPreviousPeriodDomain(hiredDomain);
        return await this.orm.searchCount('hr.applicant', hiredDomain);
    }

    async _calculateApplicantsCount(jobId = null) {
        try {
            const firstContactStage = await this.recruitmentStageService.getFirstContactStage();
            
            let applicantDomain = jobId ? [['job_id', '=', jobId]] : [];
            applicantDomain = this._addDateRangeToDomain(applicantDomain);
            
            if (firstContactStage) {
                applicantDomain.push(['stage_id.sequence', '>=', firstContactStage.sequence]);
                console.log(`✅ Calculando applicants (${jobId ? 'específico' : 'global'}): sequence >= ${firstContactStage.sequence}`);
            } else {
                console.log(`⚠️ No se encontró etapa 'Primer Contacto', contando 0`);
                return 0;
            }
            
            const count = await this.orm.searchCount(
                'hr.applicant', 
                applicantDomain,
                { context: { active_test: false } }
            ) || 0;
            
            console.log(`✅ ${jobId ? 'Específico' : 'Global'} applicants: ${count} candidatos`);
            return count;
            
        } catch (error) {
            console.error(`❌ Error calculando applicants (${jobId ? 'específico' : 'global'}):`, error);
            return 0;
        }
    }

    async _calculateGlobalHiredCount() {
        let hiredDomain = [
            ['application_status', '=', 'hired']
        ];
        hiredDomain = this._getHiredInRangeDomain(hiredDomain); // ✅ NUEVO
        return await this.orm.searchCount('hr.applicant', hiredDomain);
    }

    async _calculateGlobalRefusedMetrics() {
        let refusedDomain = [
            ['application_status', '=', 'refused']
        ];
        refusedDomain = this._addDateRangeToDomain(refusedDomain);
        
        // ✅ AGREGAR context para incluir rechazados (inactivos)
        const refusedCount = await this.orm.searchCount(
            'hr.applicant', 
            refusedDomain,
            { context: { active_test: false } }  // ✅ CLAVE: Incluir inactivos
        );

        let topRefuseReason = '';
        if (refusedCount > 0) {
            const refusedReasons = await this.orm.readGroup(
                'hr.applicant',
                refusedDomain,
                ['refuse_reason_id'],
                ['refuse_reason_id'],
                { context: { active_test: false } }  // ✅ TAMBIÉN en readGroup
            );

            if (refusedReasons.length > 0) {
                refusedReasons.sort((a, b) => b.refuse_reason_id_count - a.refuse_reason_id_count);
                const topReason = refusedReasons[0];
                topRefuseReason = topReason.refuse_reason_id ? topReason.refuse_reason_id[1] : 'Sin motivo';
            }
        }

        return { refusedCount, topRefuseReason };
    }

    async _getGlobalMetrics() {
        const [applicantsCount, hiredCount, hiredFromPreviousCount, refusedMetrics] = await Promise.all([
            this._calculateApplicantsCount(),
            this._calculateGlobalHiredCount(),
            this._calculateGlobalHiredFromPreviousPeriod(),
            this._calculateGlobalRefusedMetrics()
        ]);
        
        return {
            status: 'Global',
            openDuration: '',
            openDate: '',
            applicants: applicantsCount,
            hired: hiredCount,
            hiredFromPrevious: hiredFromPreviousCount,
            refused: refusedMetrics.refusedCount,
            topRefuseReason: refusedMetrics.topRefuseReason,
            requestedPositions: this.state.vacancyMetrics.requestedPositions
        };
    }

    _calculateVacancyStatusAndDuration(requisition) {
        const { is_published, publish_date, close_date } = requisition;
        
        let status = 'Cerrada';
        let openDuration = '';
        let openDate = ''; // ✅ NUEVO campo para fecha de apertura

        if (is_published) {
            status = 'Abierta';
            if (publish_date) {
                // ✅ Formatear fecha de apertura
                const publishDateTime = new Date(publish_date);
                openDate = publishDateTime.toLocaleDateString('es-ES', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
                
                // ✅ Calcular duración
                const startDate = new Date(publish_date);
                const endDate = close_date ? new Date(close_date) : new Date();
                const diffTime = Math.abs(endDate - startDate);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                openDuration = `${diffDays} días`;
            }
        } else if (publish_date && close_date) {
            // ✅ Para vacantes cerradas, también mostrar cuándo se abrió
            const publishDateTime = new Date(publish_date);
            openDate = publishDateTime.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            const startDate = new Date(publish_date);
            const endDate = new Date(close_date);
            const diffTime = Math.abs(endDate - startDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            openDuration = `Estuvo ${diffDays} días abierta`;
        }

        return { status, openDuration, openDate }; // ✅ DEVOLVER también openDate
    }

    async _calculateHiredCount(jobId) {
        let hiredDomain = [
            ['job_id', '=', jobId],
            ['application_status', '=', 'hired']
        ];
        hiredDomain = this._getHiredInRangeDomain(hiredDomain); // ✅ NUEVO
        return await this.orm.searchCount('hr.applicant', hiredDomain);
    }

    async _calculateRefusedMetrics(jobId) {
        let refusedDomain = [
            ['job_id', '=', jobId],
            ['application_status', '=', 'refused']
        ];
        refusedDomain = this._addDateRangeToDomain(refusedDomain);
        
        // ✅ AGREGAR context para incluir rechazados (inactivos)
        const refusedCount = await this.orm.searchCount(
            'hr.applicant', 
            refusedDomain,
            { context: { active_test: false } }  // ✅ CLAVE: Incluir inactivos
        );

        let topRefuseReason = '';
        if (refusedCount > 0) {
            const refusedReasons = await this.orm.readGroup(
                'hr.applicant',
                refusedDomain,
                ['refuse_reason_id'],
                ['refuse_reason_id'],
                { context: { active_test: false } }  // ✅ TAMBIÉN en readGroup
            );

            if (refusedReasons.length > 0) {
                refusedReasons.sort((a, b) => b.refuse_reason_id_count - a.refuse_reason_id_count);
                const topReason = refusedReasons[0];
                topRefuseReason = topReason.refuse_reason_id ? topReason.refuse_reason_id[1] : 'Sin motivo';
            }
        }

        return { refusedCount, topRefuseReason };
    }

    async _getSpecificVacancyMetrics(jobId) {
        try {
            // 1. Obtener requisiciones
            const requisitions = await this.orm.searchRead(
                'hr.requisition',
                [
                    ['workstation_job_id', '=', jobId],
                    ['state', '=', 'approved'],
                    ['is_published', '=', true]
                ],
                ['is_published', 'publish_date', 'close_date', 'number_of_vacancies']
            );

            if (requisitions.length === 0) {
                return {
                    status: 'Sin requisición',
                    openDuration: '',
                    applicants: 0,
                    hired: 0,
                    refused: 0,
                    topRefuseReason: '',
                    requestedPositions: 0
                };
            }

            // 2. Calcular status y duración
            const { status, openDuration, openDate } = this._calculateVacancyStatusAndDuration(requisitions[0]);

            // 3. Calcular posiciones solicitadas
            const requestedPositions = requisitions.reduce(
                (sum, req) => sum + (req.number_of_vacancies || 0), 0
            );

            // 4. Calcular métricas en paralelo para mejor performance
            const [applicantsCount, hiredCount, hiredFromPreviousCount, refusedMetrics] = await Promise.all([
                this._calculateApplicantsCount(jobId),
                this._calculateHiredCount(jobId),
                this._calculateHiredFromPreviousPeriod(jobId),
                this._calculateRefusedMetrics(jobId)
            ]);

            return {
                status,
                openDuration,
                openDate,
                applicants: applicantsCount,
                hired: hiredCount,
                hiredFromPrevious: hiredFromPreviousCount,
                refused: refusedMetrics.refusedCount,
                topRefuseReason: refusedMetrics.topRefuseReason,
                requestedPositions
            };

        } catch (error) {
            console.error("❌ Error calculando métricas específicas:", error);
            return {
                status: 'Error',
                openDuration: '',
                applicants: 0,
                hired: 0,
                refused: 0,
                topRefuseReason: '',
                requestedPositions: 0
            };
        }
    }

    // 🔍 ============ MANEJO DE VACANTES ============ (SIN CAMBIOS)
    onVacancyInputFocus() {
        this.state.isVacancyDropdownOpen = true;
    }

    onVacancyInputBlur() {
        setTimeout(() => {
            this.state.isVacancyDropdownOpen = false;
            if (!this.state.vacancySearchText && (!this.state.filteredVacancyOptions || !this.state.filteredVacancyOptions.length)) {
                this.selectVacancy(false);
            }
        }, 300);
    }

    selectVacancy = async (vacancy) => {
        console.log("🎯 Vacante seleccionada:", vacancy);
        
        if (!vacancy) {
            this.state.selectedVacancy = false;
            this.state.vacancySearchText = "Todas Las Vacantes";
        } else {
            this.state.selectedVacancy = vacancy.id;
            this.state.vacancySearchText = vacancy.name;
        }
        this.state.isVacancyDropdownOpen = false;

        await new Promise(resolve => setTimeout(resolve, 50));
        
        await Promise.all([
            this.getVacancyMetrics(),
            this.getFunnelRecruitment()
        ]);
    }

    clearVacancySearch() {
        this.state.vacancySearchText = "";
        this.state.filteredVacancyOptions = this.state.vacancyOptions;
        this.state.isVacancyDropdownOpen = true;
    }

    onVacancySearchInput(ev) {
        const value = ev.target.value.toLowerCase();
        this.state.vacancySearchText = ev.target.value;
        this.state.filteredVacancyOptions = this.state.vacancyOptions.filter(
            v => v.name.toLowerCase().includes(value)
        );
        this.state.isVacancyDropdownOpen = true;
    }

    async getAllVacancies() {
        try {
            // 1. Dominio base para requisiciones ABIERTAS (aprobadas y publicadas)
            let domain = [
                ['state', '=', 'approved'],
                ['is_published', '=', true]
            ];

            // 2. Buscar requisiciones que cumplen los criterios
            const openRequisitions = await this.orm.searchRead(
                'hr.requisition',
                domain,
                ['workstation_job_id', 'is_published', 'number_of_vacancies']
            );

            console.log("✅ Requisiciones abiertas encontradas:", openRequisitions.length);

            if (openRequisitions.length === 0) {
                this.state.vacancyOptions = [];
                this.state.filteredVacancyOptions = [];
                this.state.vacancySearchText = "Sin vacantes abiertas";
                this.state.vacancyMetrics.requestedPositions = 0;
                return;
            }

            // 3. Obtener IDs únicos de los jobs con vacantes abiertas
            const openJobIds = [...new Set(
                openRequisitions
                    .filter(req => req.workstation_job_id)
                    .map(req => req.workstation_job_id[0])
            )];

            if (openJobIds.length === 0) {
                this.state.vacancyOptions = [];
                this.state.filteredVacancyOptions = [];
                this.state.vacancySearchText = "Sin puestos con vacantes abiertas";
                this.state.vacancyMetrics.requestedPositions = 0;
                return;
            }

            // 4. Obtener información de los jobs
            const openJobs = await this.orm.searchRead(
                'hr.job',
                [['id', 'in', openJobIds]],
                ['id', 'name']
            );

            // 5. Calcular total de vacantes solicitadas sumando number_of_vacancies de las requisiciones abiertas
            const totalRequested = openRequisitions.reduce(
                (sum, req) => sum + (req.number_of_vacancies || 0), 0
            );
            this.state.vacancyMetrics.requestedPositions = totalRequested;

            // 6. Preparar opciones para el dropdown
            this.state.vacancyOptions = openJobs.map(j => ({
                id: j.id,
                name: j.name,
            }));
            this.state.filteredVacancyOptions = this.state.vacancyOptions;

            if (!this.state.vacancySearchText || this.state.vacancySearchText === "Sin vacantes abiertas") {
                this.state.vacancySearchText = "Todas Las Vacantes Abiertas";
            }

            console.log("✅ Vacantes abiertas cargadas:", {
                totalJobs: this.state.vacancyOptions.length,
                totalVacancies: totalRequested
            });

        } catch (error) {
            console.error("❌ FunnelChart: Error cargando vacantes abiertas:", error);
            this.state.vacancyOptions = [];
            this.state.filteredVacancyOptions = [];
            this.state.vacancySearchText = "Error cargando vacantes";
            this.state.vacancyMetrics.requestedPositions = 0;
        }
    }

    async getVacancyMetrics() {
        // await this.debugMetrics(this.state.selectedVacancy);
        if (!this.state.selectedVacancy) {
            this.state.vacancyMetrics = await this._getGlobalMetrics();
            return;
        }

        this.state.vacancyMetrics = await this._getSpecificVacancyMetrics(this.state.selectedVacancy);
    }

    // 🎪 ============ EMBUDO CON APEXCHARTS ============
    async getFunnelRecruitment() {

        try {
            // 1) Leer jobId del state
            const jobId = this.state.selectedVacancy;

            // 2) Dominio base: rango + job_id (solo si no es false)
            let baseDomain = this._addDateRangeToDomain([]);
            if (jobId) {
                baseDomain.push(['job_id', '=', jobId]);
            }

            // 3) Cargar y ordenar etapas
            const stages = await this.orm.searchRead(
                "hr.recruitment.stage", [], ["id", "name", "sequence"]
            );
            stages.sort((a, b) => a.sequence - b.sequence);

            console.log("📋 Etapas de reclutamiento:", stages);

            // 4) FUNCIÓN PARA NORMALIZAR STRINGS (solo mayúsculas/minúsculas)
            const normalizeString = (str) => {
                return str.toLowerCase().trim();
            };

            // 5) MAPEO DE ETAPAS A GRUPOS (ya en minúsculas)
            const stageGroups = [
                {
                    label: "Postulaciones",
                    stageNames: ["nuevo", "calificacion inicial", "primer contacto"],
                    minSequence: null,
                    maxSequence: null
                },
                {
                    label: "Pruebas Psicométricas", 
                    stageNames: ["pruebas psicométricas", "pruebas psicometricas", "evaluacion psicologica"],
                    minSequence: null,
                    maxSequence: null
                },
                {
                    label: "Primera Entrevista",
                    stageNames: ["primera entrevista", "entrevista inicial", "entrevista rrhh"],
                    minSequence: null,
                    maxSequence: null
                },
                {
                    label: "Entrevistas Técnicas",
                    stageNames: [
                        "examen tecnico / conocimiento", "examen técnico / conocimiento",
                        "primera entrevista / técnica", "primera entrevista / tecnica",
                        "segunda entrevista / técnica", "segunda entrevista / tecnica", 
                        "tercera entrevista / técnica", "tercera entrevista / tecnica",
                        "entrevista técnica", "entrevista tecnica"
                    ],
                    minSequence: null,
                    maxSequence: null
                },
                {
                    label: "Examen Médico",
                    stageNames: ["examen médico", "examen medico", "evaluacion médica", "evaluacion medica"],
                    minSequence: null,
                    maxSequence: null
                },
                {
                    label: "Contrataciones",
                    stageNames: ["contrato firmado", "contratado", "hired", "ofertas", "propuesta"],
                    minSequence: null,
                    maxSequence: null
                }
            ];

            // 6) Calcular min/max sequence para cada grupo usando normalización
            for (const group of stageGroups) {
                const groupStages = stages.filter(stage => 
                    group.stageNames.includes(normalizeString(stage.name))
                );
                if (groupStages.length > 0) {
                    group.minSequence = Math.min(...groupStages.map(s => s.sequence));
                    group.maxSequence = Math.max(...groupStages.map(s => s.sequence));
                    
                    console.log(`📊 Grupo "${group.label}": secuencias ${group.minSequence}-${group.maxSequence}`);
                }
            }

            // 7) Filtrar grupos válidos y ordenar por sequence
            const validGroups = stageGroups.filter(g => g.minSequence !== null);
            validGroups.sort((a, b) => a.minSequence - b.minSequence);

            console.log("✅ Grupos de etapas válidos:", validGroups.map(g => g.label));

            if (validGroups.length === 0) {
                console.log("⚠️ FunnelChart: No hay grupos válidos para el embudo");
                this.showEmptyChart();
                return;
            }

            const context = { context: { active_test: false } };

            // 8) Contar applicants para cada grupo (ACUMULATIVO)
            const counts = [];
            for (const group of validGroups) {
                const cnt = await this.orm.searchCount(
                    'hr.applicant',
                    [...baseDomain, ['stage_id.sequence', '>=', group.minSequence]],
                    context
                );
                counts.push(cnt);
            }

            // 9) ESTO ES CLAVE: Asegurar que el primer bloque tenga el total
            if (counts.length > 0) {
                // ✅ Usar la función reutilizable
                const totalApps = await this._calculateApplicantsCount(jobId);
                counts[0] = totalApps;
                
                console.log(`✅ POSTULACIONES (usando función reutilizable): ${totalApps} candidatos`);
            }

            // 10) Calcular porcentajes de conversión entre etapas consecutivas
            const conversionRates = [];
            for (let i = 0; i < counts.length; i++) {
                if (i === 0) {
                    // Primera etapa: 100% (es el total)
                    conversionRates.push(100);
                } else {
                    // Etapas siguientes: porcentaje respecto a la etapa anterior
                    const currentCount = counts[i];
                    const previousCount = counts[i - 1];
                    const conversionRate = previousCount > 0 ? ((currentCount / previousCount) * 100) : 0;
                    conversionRates.push(conversionRate);
                }
            }

            // 11) Crear datos detallados para debugging y tooltips
            const stageDetails = validGroups.map((group, index) => {
                const currentCount = counts[index];
                const conversionRate = conversionRates[index];
                const previousCount = index > 0 ? counts[index - 1] : currentCount;
                
                return {
                    label: group.label,
                    count: currentCount,
                    conversionRate: conversionRate,
                    previousCount: previousCount,
                    isFirst: index === 0,
                    group: group
                };
            });

            // 12) Log detallado para debugging
            console.log("📊 Análisis de conversión por etapas:");
            stageDetails.forEach((stage, index) => {
                if (stage.isFirst) {
                    console.log(`${index + 1}. ${stage.label}: ${stage.count} candidatos (100% - Total inicial)`);
                } else {
                    console.log(`${index + 1}. ${stage.label}: ${stage.count} candidatos (${stage.conversionRate.toFixed(1)}% de ${stage.previousCount})`);
                }
            });

            const labels = validGroups.map(g => g.label);
            const colors = this.getPastelColors(labels.length);

            // ✅ Configurar ApexChart EMBUDO con tu lógica
            this.state.chartKey = 'funnel-chart-' + Date.now();
            
            this.state.apexConfig = {
                series: [{
                    name: "Candidatos por Etapa",
                    data: counts // ✅ Datos con tu lógica acumulativa
                }],
                options: {
                    title: {
                        text: this.state.selectedVacancy ? 
                            `Embudo: ${this.state.vacancySearchText}` : 
                            'Embudo Para Todas las Vacantes',
                        align: 'center',
                        style: {
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#495057'
                        }
                    },
                    chart: {
                        type: 'bar', // ✅ Bar chart para embudo
                        height: this.props.height || 400,
                        id: 'funnel-chart-' + Date.now(),
                        dropShadow: {
                            enabled: true,
                            top: 2,
                            left: 2,
                            blur: 4,
                            opacity: 0.3
                        },
                        events: {
                            dataPointSelection: (event, chartContext, config) => {
                                const stageData = stageDetails[config.dataPointIndex];
                                if (stageData && stageData.group) {
                                    this.openGroupApplicants(stageData.group, baseDomain);
                                }
                            }
                        }
                    },
                    plotOptions: {
                        bar: {
                            borderRadius: 8,
                            horizontal: true, // ✅ Barras horizontales
                            barHeight: '75%',
                            isFunnel: true, // ✅ Efecto embudo
                            borderRadiusApplication: 'end'
                        }
                    },
                    colors: colors,
                    dataLabels: {
                        enabled: true,
                        formatter: function (val, opt) {
                            const index = opt.dataPointIndex;
                            const stage = stageDetails[index];
                            
                            // ✅ TU FORMATO: Nombre, cantidad y porcentaje de conversión
                            if (stage.isFirst) {
                                return `${stage.label}: ${stage.count} (100%)`;
                            } else {
                                return `${stage.label}: ${stage.count} (${stage.conversionRate.toFixed(0)}%)`;
                            }
                        },
                        style: {
                            fontSize: '12px',
                            fontWeight: 'bold',
                            colors: ['#fff']
                        },
                        dropShadow: {
                            enabled: true,
                            top: 1,
                            left: 1,
                            blur: 2,
                            opacity: 0.5
                        }
                    },
                    xaxis: {
                        categories: labels,
                        labels: {
                            style: {
                                fontSize: '11px',
                                fontWeight: 'bold',
                                colors: ['#495057']
                            }
                        }
                    },
                    yaxis: {
                        labels: {
                            style: {
                                fontSize: '11px',
                                fontWeight: 'bold',
                                colors: ['#495057']
                            }
                        }
                    },
                    legend: {
                        show: false
                    },
                    tooltip: {
                        y: {
                            formatter: function(value, { dataPointIndex }) {
                                const stage = stageDetails[dataPointIndex];
                                
                                if (stage.isFirst) {
                                    return `<strong>${stage.label}</strong><br/>
                                            ${stage.count} candidatos (Total inicial)<br/>
                                            <em>Haz clic para ver detalles</em>`;
                                } else {
                                    const lost = stage.previousCount - stage.count;
                                    const lossRate = ((lost / stage.previousCount) * 100).toFixed(1);
                                    
                                    return `<strong>${stage.label}</strong><br/>
                                            ${stage.count} candidatos (${stage.conversionRate.toFixed(1)}% de ${stage.previousCount})<br/>
                                            Perdidos en esta etapa: ${lost} candidatos (${lossRate}%)<br/>
                                            <em>Haz clic para ver detalles</em>`;
                                }
                            }
                        },
                        theme: 'dark'
                    },
                    grid: {
                        show: true,
                        borderColor: '#f1f1f1',
                        strokeDashArray: 3,
                        xaxis: {
                            lines: { show: true }
                        },
                        yaxis: {
                            lines: { show: false }
                        }
                    },
                    responsive: [{
                        breakpoint: 768,
                        options: {
                            plotOptions: {
                                bar: { barHeight: '60%' }
                            },
                            dataLabels: {
                                formatter: function (val, opt) {
                                    return `${val}`;
                                },
                                style: { fontSize: '10px' }
                            }
                        }
                    }]
                }
            };

            this.state.funnelRecruitment = {
                labels,
                data: counts,
                total: counts[0] || 0,
                stageDetails: stageDetails // ✅ TUS datos detallados
            };

            this.state.hasData = true;

            // ✅ TU log final con resumen
            console.log("✅ Embudo de conversión actualizado:");
            console.log(`   Total inicial: ${counts[0]} candidatos`);
            if (conversionRates.length > 1) {
                const avgConversion = (conversionRates.slice(1).reduce((sum, rate) => sum + rate, 0) / (conversionRates.length - 1)).toFixed(1);
                console.log(`   Conversión promedio: ${avgConversion}%`);
            }
            console.log(`   Candidatos finales: ${counts[counts.length - 1]} (${((counts[counts.length - 1] / counts[0]) * 100).toFixed(1)}% del total)`);

        } catch (error) {
            console.error("❌ FunnelChart: Error cargando embudo:", error);
            this.showEmptyChart();
        }
    }

    // ✅ NUEVO: Método para abrir postulaciones de un grupo de etapas
    async openGroupApplicants(group, baseDomain) {
        console.log("🔍 FunnelChart: Abriendo postulaciones del grupo:", group.label);
        
        let domain = [...baseDomain, ['stage_id.sequence', '>=', group.minSequence]];

        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Postulaciones: ${group.label}`,
            res_model: 'hr.applicant',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            domain: domain,
            context: { active_test: false }
        });
    }

    showEmptyChart() {
        this.state.hasData = false;
        this.state.chartKey = 'empty-funnel-' + Date.now();
        
        this.state.apexConfig = {
            series: [{
                name: "Sin datos",
                data: [1] // ✅ Para bar chart necesitamos data array
            }],
            options: {
                chart: {
                    type: 'bar',
                    height: this.props.height || 400,
                    id: 'empty-funnel-chart-' + Date.now()
                },
                plotOptions: {
                    bar: {
                        horizontal: true,
                        barHeight: '40%',
                        isFunnel: true
                    }
                },
                xaxis: {
                    categories: ['Sin datos']
                },
                colors: ['#E0E0E0'],
                dataLabels: { enabled: false },
                legend: { show: false },
                tooltip: { enabled: false },
                title: {
                    text: 'No hay datos disponibles',
                    align: 'center',
                    style: { color: '#999' }
                },
                grid: { show: false }
            }
        };
        
        this.state.funnelRecruitment = { labels: [], data: [], total: 0 };
    }

    async openStageApplicants(stageId) {
        console.log("🔍 FunnelChart: Abriendo postulaciones de etapa:", stageId);
        
        const currentProps = this.getCurrentProps();
        let domain = [['stage_id', '=', stageId]];
        domain = this._addDateRangeToDomain(domain);

        if (this.state.selectedVacancy) {
            domain.push(['job_id', '=', this.state.selectedVacancy]);
        }

        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Postulaciones por Etapa',
            res_model: 'hr.applicant',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            domain: domain,
            context: { active_test: false }
        });
    }

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

    async refresh() {
        console.log("🔄 FunnelChart: Iniciando refresh...");
        this.showEmptyChart();
        await new Promise(resolve => setTimeout(resolve, 100));
        await this.loadFunnelData();
        console.log("✅ FunnelChart: Refresh completado");
    }
}