/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { DashboardHeader } from "./dashboard_header/dashboard_header";
import { KpisGrid } from "./kpis/kpis_grid";
import { RecruiterEfficiencyChart } from "./charts/recruiter_efficiency_chart/recruiter_efficiency_chart";
import { ProcessEfficiencyChart } from "./charts/process_efficiency_chart/process_efficiency_chart";
import { RecruitmentSourcesChart } from "./charts/recruitment_sources_chart/recruitment_sources_chart";


import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { RejectionReasonsChart } from "./charts/rejection_reasons_chart/rejection_reasons_chart";
const { DateTime } = luxon;

export class RecruitmentDashboard extends Component {

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        // ✅ Variables para referencias de componentes
        this.kpisGridComponent = null;
        this.recruiterEfficiencyComponent = null;
        this.processEfficiencyComponent = null;
        this.recruitmentSourcesComponent = null;
        this.rejectionReasonsComponent = null;

        this.state = useState({
            // Filtros
            startDate: "",
            endDate: "",
            selectedVacancy: false,
            availableVacancies: [],
            funnelRecruitment: {},
            requisitionStats: {},
            vacancyOptions: [],
            filteredVacancyOptions: [],
            vacancySearchText: "Todas Las Vacantes",
            isVacancyDropdownOpen: false,
            vacancyMetrics: {
                status: 'Global',
                openDuration: '',
                applicants: 0,
                hired: 0,
                refused: 0,
                topRefuseReason: ''
            }
        });

        // ✅ Cargar datos al inicializar
        onWillStart(async () => {
            // Inicializar fechas por defecto
            const today = new Date();
            const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
            this.state.startDate = firstDayOfMonth.toISOString().split('T')[0];
            this.state.endDate = today.toISOString().split('T')[0];

            // Cargar datos del dashboard (sin KPIs)
            await this.loadAllData();
        });
    }

    _addDateRangeToDomain(domain = []) {
        if (this.state.startDate) {
            domain.push(["create_date", ">=", this.state.startDate]);
        }
        if (this.state.endDate) {
            domain.push(["create_date", "<=", this.state.endDate]);
        }
        return domain;
    }

    _getHiredDateRangeDomain(domain = []) {
        if (this.state.startDate) {
            domain.push(["date_closed", ">=", this.state.startDate]);
        }
        if (this.state.endDate) {
            domain.push(["date_closed", "<=", this.state.endDate]);
        }
        return domain;
    }

    // ✅ Callbacks de montaje de componentes
    onKpisGridMounted(kpisGridComponent) {
        console.log("📊 Dashboard: KpisGrid montado", kpisGridComponent);
        this.kpisGridComponent = kpisGridComponent;
    }

    onRecruiterEfficiencyMounted(recruiterEfficiencyComponent) {
        console.log("📊 Dashboard: RecruiterEfficiencyChart montado", recruiterEfficiencyComponent);
        this.recruiterEfficiencyComponent = recruiterEfficiencyComponent;
    }

    onProcessEfficiencyMounted(processEfficiencyComponent) {
        console.log("📊 Dashboard: ProcessEfficiencyChart montado", processEfficiencyComponent);
        this.processEfficiencyComponent = processEfficiencyComponent;
    }

    onRecruitmentSourcesMounted(recruitmentSourcesComponent) {
        console.log("📊 Dashboard: RecruitmentSourcesChart montado", recruitmentSourcesComponent);
        this.recruitmentSourcesComponent = recruitmentSourcesComponent;
    }

    openRejectionDetails = (reason) => {
        // Ejemplo: mostrar modal con detalles
        this.setState({
            showRejectionModal: true,
            selectedReason: reason
        });
        
        // O cargar datos relacionados:
        // fetchCandidatesByReason(reason.id).then(data => {...})
    }

    onRejectionReasonsMounted(rejectionReasonsComponent) {
        console.log("📊 Dashboard: RejectionReasonsChart montado", rejectionReasonsComponent);
        this.rejectionReasonsComponent = rejectionReasonsComponent;
    }

    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false) {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);

        domain.push(["user_id", "=", userId]);

        // ✅ NUEVO: Filtrar por tipo de aplicación
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

    async openRequisitionList(stateCode) {
        let domain = [];
        domain = this._addDateRangeToDomain(domain);
        if (stateCode === 'approved_open') {
            domain.push(['state', '=', 'approved'], ['is_published', '=', true]);
        } else if (stateCode === 'approved_closed') {
            domain.push(['state', '=', 'approved'], ['is_published', '=', false]);
        } else if (stateCode) {
            domain.push(['state', '=', stateCode]);
        }
        await this.actionService.doAction({
        type: 'ir.actions.act_window',
        name: 'Requisiciones',
        res_model: 'hr.requisition',
        views: [[false,'list'],[false,'form']],
        domain: domain,
        });
    }

    onVacancyInputFocus() {
        this.state.isVacancyDropdownOpen = true;
    }

    onVacancyInputBlur() {
        setTimeout(() => {
            this.state.isVacancyDropdownOpen = false;
            // Si el input quedó vacío, selecciona "Todas Las Vacantes"
            // Solo selecciona "Todas Las Vacantes" si el input está vacío Y no hay opciones filtradas
            if (!this.state.vacancySearchText && (!this.state.filteredVacancyOptions || !this.state.filteredVacancyOptions.length)) {
                this.selectVacancy(false);
            }
        }, 300);
    }

    selectVacancy = async (vacancy) => {
        console.log("Vacancy selected:", vacancy);
        if (!vacancy) {
            this.state.selectedVacancy = false;
            this.state.vacancySearchText = "Todas Las Vacantes";
        } else {
            this.state.selectedVacancy = vacancy.id;
            this.state.vacancySearchText = vacancy.name;
        }
        this.state.isVacancyDropdownOpen = false;

        // Esperar a que OWL actualice el estado antes de cargar datos
        await new Promise(resolve => setTimeout(resolve, 50));
        
        // Recargar datos
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

    async onDateRangeChange(startDate, endDate) {
        
        this.state.startDate = startDate;
        this.state.endDate = endDate;
        
        // ✅ CREAR array para promises de recarga
        const reloadPromises = [];
        
        if (this.kpisGridComponent) {
            reloadPromises.push(this.kpisGridComponent.loadKpisData());
        }

        if (this.recruiterEfficiencyComponent) {
            reloadPromises.push(this.recruiterEfficiencyComponent.loadChartData());
        }

        if (this.processEfficiencyComponent) {
            reloadPromises.push(this.processEfficiencyComponent.refresh());
        }

        if (this.recruitmentSourcesComponent) {
            console.log("🔄 Dashboard: Recargando fuentes de reclutamiento...");
            reloadPromises.push(this.recruitmentSourcesComponent.refresh());
        }

        if (this.rejectionReasonsComponent) {
            console.log("🔄 Dashboard: Recargando motivos de rechazo...");
            reloadPromises.push(this.rejectionReasonsComponent.refresh());
        }
        
        // ✅ ESPERAR todas las recargas en paralelo
        await Promise.all(reloadPromises);
        
        // Recargar datos de gráficos del dashboard
        await this.loadAllData();
    }

    async loadAllData() {
        try {
            await Promise.all([
                this.getAllVacancies(),
                this.getVacancyMetrics(),
                this.getFunnelRecruitment(),
                this.getRequisitionStats(),
            ]);
            console.log("✅ Dashboard: Todos los datos cargados");
        } catch (error) {
            console.error("❌ Dashboard: Error cargando datos:", error);
        }
    }

    async getAllVacancies() {
        console.log("📋 Cargando vacantes con requisiciones aprobadas...");
        
        try {
            // 1) Primero obtener todas las requisiciones aprobadas
            const approvedRequisitions = await this.orm.searchRead(
                'hr.requisition',
                [['state', '=', 'approved']],  // ✅ Solo requisiciones aprobadas
                ['workstation_job_id', 'is_published', 'publish_date', 'close_date']
            );
            
            console.log("✅ Requisiciones aprobadas encontradas:", approvedRequisitions.length);
            
            if (approvedRequisitions.length === 0) {
                console.log("⚠️ No hay requisiciones aprobadas, lista de vacantes vacía");
                this.state.vacancyOptions = [];
                this.state.filteredVacancyOptions = [];
                this.state.vacancySearchText = "Sin vacantes disponibles";
                return;
            }
            
            // 2) Extraer los IDs únicos de workstation_job_id (eliminar duplicados)
            const approvedJobIds = [...new Set(
                approvedRequisitions
                    .filter(req => req.workstation_job_id)  // Solo los que tienen job
                    .map(req => req.workstation_job_id[0])   // Extraer el ID
            )];
            
            console.log("🎯 IDs de trabajos con requisiciones aprobadas:", approvedJobIds);
            
            if (approvedJobIds.length === 0) {
                console.log("⚠️ No hay trabajos asociados a requisiciones aprobadas");
                this.state.vacancyOptions = [];
                this.state.filteredVacancyOptions = [];
                this.state.vacancySearchText = "Sin vacantes disponibles";
                return;
            }
            
            // 3) Obtener los datos de los trabajos (hr.job) que tienen requisiciones aprobadas
            const approvedJobs = await this.orm.searchRead(
                'hr.job',
                [['id', 'in', approvedJobIds]],  // ✅ Solo jobs con requisiciones aprobadas
                ['id', 'name']
            );
            
            console.log("✅ Vacantes con requisiciones aprobadas:", approvedJobs.length);
            
            // 4) Actualizar el estado
            this.state.vacancyOptions = approvedJobs.map(j => ({
                id: j.id,
                name: j.name,
            }));
            this.state.filteredVacancyOptions = this.state.vacancyOptions;
            
            // 5) Inicializar el texto del selector
            if (!this.state.vacancySearchText || this.state.vacancySearchText === "Sin vacantes disponibles") {
                this.state.vacancySearchText = "Todas Las Vacantes";
            }
            
            console.log("✅ Vacantes cargadas:", this.state.vacancyOptions.length);
            
        } catch (error) {
            console.error("❌ Error cargando vacantes con requisiciones aprobadas:", error);
            this.state.vacancyOptions = [];
            this.state.filteredVacancyOptions = [];
            this.state.vacancySearchText = "Error cargando vacantes";
        }
    }

    getPastelColors(count) {
        // Paleta de colores premium más vivos (12 colores base)
        const premiumColors = [
            '#4ECDC4', // Turquesa elegante
            '#45B7D1', // Azul cielo premium
            '#96CEB4', // Verde menta sofisticado
            '#FFEAA7', // Amarillo dorado suave
            '#DDA0DD', // Lavanda premium
            '#FFB347', // Naranja mandarina
            '#98D8C8', // Verde agua cristalina
            '#F7DC6F', // Oro pálido
            '#BB8FCE', // Púrpura elegante
            '#85C1E9', // Azul cielo claro
            '#F8C471', // Melocotón dorado
            '#FF6B6B', // Rojo coral vibrante
        ];

        // Si necesitas 12 o menos colores, usa la paleta predefinida
        if (count <= premiumColors.length) {
            return premiumColors.slice(0, count);
        }

        // Para más de 12 colores, combina la paleta base + colores generados dinámicamente
        const colors = [...premiumColors];
        
        // Genera colores adicionales con valores más vivos y distribuidos
        for (let i = premiumColors.length; i < count; i++) {
            // Distribuye los matices uniformemente en el círculo cromático
            const hue = Math.floor((360 / (count - premiumColors.length)) * (i - premiumColors.length));
            
            // Saturación alta para colores vivos (65-85%)
            const saturation = 65 + Math.random() * 20;
            
            // Luminosidad premium (55-75%)
            const lightness = 55 + Math.random() * 20;
            
            colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }
        
        return colors;
    }

    async getFunnelRecruitment() {
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

        console.log("Etapas de reclutamiento:", stages);

        // 4) **FUNCIÓN PARA NORMALIZAR STRINGS (solo mayúsculas/minúsculas)**
        const normalizeString = (str) => {
            return str.toLowerCase().trim();
        };

        // 5) **MAPEO DE ETAPAS A GRUPOS (ya en minúsculas)**
        const stageGroups = [
            {
                label: "Aplicaciones",
                stageNames: ["nuevo", "calificacion inicial", "primer contacto"],
                minSequence: null,
                maxSequence: null
            },
            {
                label: "Pruebas Psicométricas", 
                stageNames: ["pruebas psicométricas"],
                minSequence: null,
                maxSequence: null
            },
            {
                label: "Primera Entrevista",
                stageNames: ["primera entrevista"],
                minSequence: null,
                maxSequence: null
            },
            {
                label: "Examen Técnico",
                stageNames: [
                    "examen técnico / conocimiento", 
                    "primera entrevista / técnica", 
                    "segunda entrevista / técnica", 
                    "tercera entrevista / técnica"
                ],
                minSequence: null,
                maxSequence: null
            },
            {
                label: "Entrevista Técnica",
                stageNames: [
                    "primera entrevista / técnica", 
                    "segunda entrevista / técnica", 
                    "tercera entrevista / técnica"
                ],
                minSequence: null,
                maxSequence: null
            },
            {
                label: "Examen Médico",
                stageNames: ["examen médico"],
                minSequence: null,
                maxSequence: null
            },
            {
                label: "Contrataciones",
                stageNames: ["contrato firmado"],
                minSequence: null,
                maxSequence: null
            }
        ];

        // 6) **Calcular min/max sequence para cada grupo usando normalización**
        for (const group of stageGroups) {
            const groupStages = stages.filter(stage => 
                group.stageNames.includes(normalizeString(stage.name))
            );
            if (groupStages.length > 0) {
                group.minSequence = Math.min(...groupStages.map(s => s.sequence));
                group.maxSequence = Math.max(...groupStages.map(s => s.sequence));
            }
        }

        // 7) Filtrar grupos válidos y ordenar por sequence
        const validGroups = stageGroups.filter(g => g.minSequence !== null);
        validGroups.sort((a, b) => a.minSequence - b.minSequence);

        console.log("Grupos de etapas válidos:", validGroups);

        // 8) Contar applicants para cada grupo
        const counts = [];
        for (const group of validGroups) {
            const cnt = await this.orm.searchCount(
                'hr.applicant',
                [...baseDomain, ['stage_id.sequence', '>=', group.minSequence]]
            );
            counts.push(cnt);
        }

        // 9) **ESTO ES CLAVE: Asegurar que el primer bloque tenga el total**
        if (counts.length > 0) {
            const totalApps = await this.orm.searchCount('hr.applicant', baseDomain) || 0;
            counts[0] = totalApps;
        }

        // ✅ **10) NUEVO: Calcular porcentajes de conversión entre etapas consecutivas**
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

        // ✅ **11) Crear datos detallados para debugging y tooltips**
        const stageDetails = validGroups.map((group, index) => {
            const currentCount = counts[index];
            const conversionRate = conversionRates[index];
            const previousCount = index > 0 ? counts[index - 1] : currentCount;
            
            return {
                label: group.label,
                count: currentCount,
                conversionRate: conversionRate,
                previousCount: previousCount,
                isFirst: index === 0
            };
        });

        // ✅ **12) Log detallado para debugging**
        console.log("📊 Análisis de conversión por etapas:");
        stageDetails.forEach((stage, index) => {
            if (stage.isFirst) {
                console.log(`${index + 1}. ${stage.label}: ${stage.count} candidatos (100% - Total inicial)`);
            } else {
                console.log(`${index + 1}. ${stage.label}: ${stage.count} candidatos (${stage.conversionRate.toFixed(1)}% de ${stage.previousCount})`);
            }
        });

        // 13) Labels, colores, opciones
        const labels = validGroups.map(g => g.label);
        const colors = this.getPastelColors(labels.length);
        
        const options = {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 1.2,
            plugins: {
                legend: { display: false },
                tooltip: { 
                    callbacks: {
                        label: ctx => {
                            const index = ctx.dataIndex;
                            const stage = stageDetails[index];
                            
                            if (stage.isFirst) {
                                return `${stage.label}: ${stage.count} candidatos (Total inicial)`;
                            } else {
                                return `${stage.label}: ${stage.count} candidatos (${stage.conversionRate.toFixed(1)}% de ${stage.previousCount})`;
                            }
                        },
                        // ✅ NUEVO: Información adicional en el tooltip
                        afterBody: (context) => {
                            const index = context[0].dataIndex;
                            const stage = stageDetails[index];
                            
                            if (!stage.isFirst) {
                                const lost = stage.previousCount - stage.count;
                                const lossRate = ((lost / stage.previousCount) * 100).toFixed(1);
                                return [
                                    `Perdidos en esta etapa: ${lost} candidatos (${lossRate}%)`,
                                    `Venían de: ${stage.previousCount} candidatos`
                                ];
                            }
                            return [];
                        }
                    }
                },
                datalabels: {
                    anchor: 'center', 
                    align: 'center',
                    color: '#fff', 
                    font: { weight: 'bold', size: 12 },
                    backgroundColor: 'rgba(0,0,0,0.6)',
                    padding: { top: 4, bottom: 4, left: 6, right: 6 },
                    formatter: (val, ctx) => {
                        const index = ctx.dataIndex;
                        const stage = stageDetails[index];
                        
                        // ✅ NUEVO: Mostrar nombre, cantidad y porcentaje de conversión
                        if (stage.isFirst) {
                            return `${stage.label}\n${stage.count}\n100%`;
                        } else {
                            return `${stage.label}\n${stage.count}\n${stage.conversionRate.toFixed(0)}%`;
                        }
                    }
                }
            }
        };

        // 14) Actualizar estado
        this.state.funnelRecruitment = {
            data: { 
                labels, 
                datasets: [{ 
                    data: counts, 
                    backgroundColor: colors 
                }] 
            },
            options,
            enableDataLabels: true,
            // ✅ NUEVO: Guardar datos detallados para uso posterior
            stageDetails: stageDetails
        };

        // ✅ **15) Log final con resumen**
        console.log("✅ Embudo de conversión actualizado:");
        console.log(`   Total inicial: ${counts[0]} candidatos`);
        console.log(`   Conversión promedio: ${(conversionRates.slice(1).reduce((sum, rate) => sum + rate, 0) / (conversionRates.length - 1)).toFixed(1)}%`);
        console.log(`   Candidatos finales: ${counts[counts.length - 1]} (${((counts[counts.length - 1] / counts[0]) * 100).toFixed(1)}% del total)`);
    }

    async getRequisitionStats() {
        let domain = [];
        domain = this._addDateRangeToDomain(domain);
    
        const data = await this.orm.readGroup(
            'hr.requisition',
            domain,
            ['state'],
            ['state']
        );
        //Convertir a un map
        const countMap = {};
        data.forEach(r => {
          countMap[r.state] = r.state_count;
        });
        //Definir labels y conteos en orden
        const labels = [
          'Total',
          'Por Activar',  // to_approve
          'Abiertas',     // approved & is_published = true
          'Cerradas'      // approved & is_published = false
        ];
        // Total = suma de todos
        const total = data.reduce((sum, r) => sum + r.state_count, 0);
        // Contar cada estado
        const countToApprove = countMap['to_approve'] || 0;
        const countApprovedOpen = await this.orm.searchCount(
          'hr.requisition',
          [...domain, ['state', '=', 'approved'], ['is_published', '=', true]]
        );
        const countApprovedClosed = await this.orm.searchCount(
          'hr.requisition',
          [...domain, ['state', '=', 'approved'], ['is_published', '=', false]]
        );

        const meta = [
          { state: null },               // para “Total”
          { state: 'to_approve' },
          { state: 'approved_open' },    // código interno
          { state: 'approved_closed' },
        ];
        const counts = [
          total,
          countToApprove,
          countApprovedOpen,
          countApprovedClosed,
        ];
    
        this.state.requisitionStats = {
          data: {
            labels,
            datasets: [{
              label: 'Requisiciones',
              data: counts,
              backgroundColor: this.getPastelColors(labels.length),
            }]
          },
          meta,
          options: {
            indexAxis: 'x',
            scales: {
                x: {
                  beginAtZero: true,
                  ticks: { autoSkip: false }
                },
                y: {
                  beginAtZero: true,
                },
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        generateLabels: chart => {
                            // labels[] = ['Total','Por Activar','Abiertas','Cerradas']
                            // backgroundColor[] = color por cada barra
                            const data = chart.data;
                            return data.labels.map((lbl, i) => ({
                                text: lbl,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                hidden: chart.getDataVisibility(i) === false,
                                index: i,
                            }));
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${labels[ctx.dataIndex]}: ${counts[ctx.dataIndex]}`
                    }
                }
            },
            onClick: (event, active) => {
              if (!active.length) return;
              const idx = active[0].index;
              const item = this.state.requisitionStats.meta[idx];
              this.openRequisitionList(item.state);
            },
            plugins: {
              tooltip: {
                callbacks: {
                  label: ctx => `${labels[ctx.dataIndex]}: ${counts[ctx.dataIndex]}`
                }
              }
            }
          }
        };
        // fuerza el update
        this.state.requisitionStats = { ...this.state.requisitionStats };
    }    

    async getVacancyMetrics() {
        // Leer el job seleccionado y parsear a número
        const rawJid = this.state.selectedVacancy;
        const jobId  = rawJid && rawJid !== 'false' ? parseInt(rawJid, 10) : null;
    
        // Obtener la última requisición aprobada para ese job
        let lastReq = null;
        if (jobId) {
            const reqs = await this.orm.searchRead(
                'hr.requisition',
                [
                    ['workstation_job_id', '=', jobId],
                    ['state', '=', 'approved'],
                ],
                ['publish_date','close_date'],
                { order: 'publish_date desc', limit: 1 }
            );
            lastReq = reqs[0] || null;
        }
    
        const baseDomain = this._addDateRangeToDomain([]);
        if (jobId) {
            baseDomain.push(['job_id','=', jobId]);
        }
        const rpcContext = { context: { active_test: false } };
    
        // Declarar variables de métricas
        let totalApps = 0, hired = 0, refused = 0;
        let topReason = '';
        let status    = 'Global';
        let openDur   = '';
    
        // Contar applicants
        totalApps = await this.orm.searchCount('hr.applicant', baseDomain, rpcContext);
        hired     = await this.orm.searchCount('hr.applicant', [...baseDomain, ['application_status','=', 'hired']], rpcContext);
        refused   = await this.orm.searchCount('hr.applicant', [...baseDomain, ['application_status','=', 'refused']], rpcContext);
    
        // Agrupar motivos de rechazo
        const rg = await this.orm.readGroup(
            'hr.applicant',
            [...baseDomain, ['application_status','=', 'refused']],
            ['refuse_reason_id'],
            ['refuse_reason_id'],
            rpcContext
        );
        if (rg.length) {
            rg.sort((a, b) => b.refuse_reason_id_count - a.refuse_reason_id_count);
            topReason = rg[0].refuse_reason_id[1] || '';
        }
    
        // Estado y duración según la última requisición aprobada
        if (lastReq && lastReq.publish_date) {
            // Parseamos publish_date y close_date
            let pubDT = DateTime.fromISO(lastReq.publish_date);
            if (!pubDT.isValid) {
                pubDT = DateTime.fromJSDate(new Date(lastReq.publish_date));
            }
            let closeDT = lastReq.close_date
                ? DateTime.fromISO(lastReq.close_date)
                : null;
            if (lastReq.close_date && (!closeDT || !closeDT.isValid)) {
                closeDT = DateTime.fromJSDate(new Date(lastReq.close_date));
            }
        
            // Fecha "base" de comparación: hoy
            const nowDT = DateTime.now();
        
            // Si está cerrada, tiempo desde closeDT hasta hoy
            // Si está abierta, tiempo desde pubDT hasta hoy
            const startDT = closeDT ? closeDT : pubDT;
            status = closeDT ? 'Cerrada' : 'Abierta';
        
            // Calculamos diff sobre nowDT - startDT
            const diff = nowDT.diff(startDT, ['days','hours']).toObject();
            const days  = Math.floor(diff.days  || 0);
            const hours = Math.floor(diff.hours || 0);
        
            // Formateamos
            openDur = `${days} día${days !== 1 ? 's' : ''}`;
            if (hours) {
                openDur += ` y ${hours} hora${hours !== 1 ? 's' : ''}`;
            }
        } else if (jobId) {
            status  = 'Por Activar';
            openDur = '';
        }
    
        // Actualizar el state
        this.state.vacancyMetrics = {
            status,
            openDuration:   openDur,
            applicants:     totalApps,
            hired,
            refused,
            topRefuseReason: topReason,
        };
    }

}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = {
    DashboardHeader, KpisGrid, 
    ChartRenderer, RecruiterEfficiencyChart,
    ProcessEfficiencyChart, RecruitmentSourcesChart,
    RejectionReasonsChart
};

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);