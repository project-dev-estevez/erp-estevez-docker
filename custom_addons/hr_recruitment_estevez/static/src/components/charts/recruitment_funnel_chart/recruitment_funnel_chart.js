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
                applicants: 0,
                hired: 0,
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
        const currentProps = this.getCurrentProps();
        
        console.log("🎪 RecruitmentFunnelChart: Cargando datos del embudo...", {
            startDate: currentProps.startDate,
            endDate: currentProps.endDate
        });

        this.state.isLoading = true;

        try {
            await Promise.all([
                this.getAllVacancies(),
                this.getVacancyMetrics(),
                this.getFunnelRecruitment()
            ]);
            console.log("✅ RecruitmentFunnelChart: Datos cargados correctamente");
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
            const currentProps = this.getCurrentProps();

            // 1. Dominio base para requisiciones ABIERTAS (aprobadas y publicadas)
            // SIN filtro de fechas de publicación
            let domain = [
                ['state', '=', 'approved'],
                ['is_published', '=', true]
            ];

            console.log("🔍 Dominio para requisiciones abiertas:", domain);

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
        if (!this.state.selectedVacancy) {
            this.state.vacancyMetrics = {
                status: 'Global',
                openDuration: '',
                applicants: 0,
                hired: 0,
                refused: 0,
                topRefuseReason: '',
                requestedPositions: this.state.vacancyMetrics.requestedPositions // Mantiene el total global
            };
            return;
        }

        try {
            const requisitions = await this.orm.searchRead(
                'hr.requisition',
                [
                    ['workstation_job_id', '=', this.state.selectedVacancy],
                    ['state', '=', 'approved'],
                    ['is_published', '=', true] // Solo requisiciones publicadas
                ],
                ['is_published', 'publish_date', 'close_date', 'number_of_vacancies']
            );

            if (requisitions.length === 0) {
                this.state.vacancyMetrics = {
                    status: 'Sin requisición',
                    openDuration: '',
                    applicants: 0,
                    hired: 0,
                    refused: 0,
                    topRefuseReason: '',
                    requestedPositions: 0 // Sin requisición = 0 vacantes
                };
                return;
            }

            // Tomar la primera requisición (o sumar si hay múltiples)
            const requisition = requisitions[0];
            const isPublished = requisition.is_published;
            const publishDate = requisition.publish_date;
            const closeDate = requisition.close_date;

            // Calcular vacantes solicitadas específicas para este puesto
            const specificRequestedPositions = requisitions.reduce(
                (sum, req) => sum + (req.number_of_vacancies || 0), 0
            );

            let status = 'Cerrada';
            let openDuration = '';

            if (isPublished) {
                status = 'Abierta';
                if (publishDate) {
                    const startDate = new Date(publishDate);
                    const endDate = closeDate ? new Date(closeDate) : new Date();
                    const diffTime = Math.abs(endDate - startDate);
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    openDuration = `${diffDays} días`;
                }
            } else if (publishDate && closeDate) {
                const startDate = new Date(publishDate);
                const endDate = new Date(closeDate);
                const diffTime = Math.abs(endDate - startDate);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                openDuration = `Estuvo ${diffDays} días abierta`;
            }

            let applicantDomain = [['job_id', '=', this.state.selectedVacancy]];
            applicantDomain = this._addDateRangeToDomain(applicantDomain);
            const applicantsCount = await this.orm.searchCount('hr.applicant', applicantDomain);

            let hiredDomain = [
                ['job_id', '=', this.state.selectedVacancy],
                ['application_status', '=', 'hired']
            ];
            hiredDomain = this._getHiredDateRangeDomain(hiredDomain);
            const hiredCount = await this.orm.searchCount('hr.applicant', hiredDomain);

            let refusedDomain = [
                ['job_id', '=', this.state.selectedVacancy],
                ['application_status', '=', 'refused']
            ];
            refusedDomain = this._addDateRangeToDomain(refusedDomain);
            const refusedCount = await this.orm.searchCount('hr.applicant', refusedDomain);

            let topRefuseReason = '';
            if (refusedCount > 0) {
                const refusedReasons = await this.orm.readGroup(
                    'hr.applicant',
                    refusedDomain,
                    ['refuse_reason_id'],
                    ['refuse_reason_id']
                );

                if (refusedReasons.length > 0) {
                    refusedReasons.sort((a, b) => b.refuse_reason_id_count - a.refuse_reason_id_count);
                    const topReason = refusedReasons[0];
                    topRefuseReason = topReason.refuse_reason_id ? topReason.refuse_reason_id[1] : 'Sin motivo';
                }
            }

            this.state.vacancyMetrics = {
                status,
                openDuration,
                applicants: applicantsCount,
                hired: hiredCount,
                refused: refusedCount,
                topRefuseReason,
                requestedPositions: specificRequestedPositions // ✅ Número específico del puesto
            };

        } catch (error) {
            console.error("❌ FunnelChart: Error cargando métricas de vacante:", error);
            this.state.vacancyMetrics = {
                status: 'Error',
                openDuration: '',
                applicants: 0,
                hired: 0,
                refused: 0,
                topRefuseReason: '',
                requestedPositions: 0 // Error = 0 vacantes
            };
        }
    }

    // 🎪 ============ EMBUDO CON APEXCHARTS ============
    async getFunnelRecruitment() {
        console.log("🎪 FunnelChart: Cargando datos del embudo con lógica de grupos...");
        
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
                    label: "Aplicaciones",
                    stageNames: ["nuevo", "calificacion inicial", "primer contacto", "aplicacion inicial"],
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
                    label: "Examen Técnico",
                    stageNames: [
                        "examen técnico", "examen tecnico", "prueba técnica", "prueba tecnica",
                        "evaluacion técnica", "evaluacion tecnica", "conocimiento técnico"
                    ],
                    minSequence: null,
                    maxSequence: null
                },
                {
                    label: "Entrevista Técnica",
                    stageNames: [
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

            // 8) Contar applicants para cada grupo (ACUMULATIVO)
            const counts = [];
            for (const group of validGroups) {
                const cnt = await this.orm.searchCount(
                    'hr.applicant',
                    [...baseDomain, ['stage_id.sequence', '>=', group.minSequence]]
                );
                counts.push(cnt);
            }

            // 9) ESTO ES CLAVE: Asegurar que el primer bloque tenga el total
            if (counts.length > 0) {
                const totalApps = await this.orm.searchCount('hr.applicant', baseDomain) || 0;
                counts[0] = totalApps;
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
                            'Embudo: Todas las Vacantes',
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