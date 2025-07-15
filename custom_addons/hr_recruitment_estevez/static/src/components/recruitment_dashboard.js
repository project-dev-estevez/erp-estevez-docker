/** @odoo-module **/

import { registry } from "@web/core/registry";

import { DashboardHeader } from "./dashboard_header/dashboard_header";
import { KpisGrid } from "./kpis/kpis_grid";

import { RecruiterEfficiencyChart } from "./charts/recruiter_efficiency_chart/recruiter_efficiency_chart";

import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
const { DateTime } = luxon;

export class RecruitmentDashboard extends Component {

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

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        // ✅ Variables para referencias de componentes
        this.kpisGridComponent = null;
        this.recruiterEfficiencyComponent = null;

        // ✅ Estado del dashboard - YA NO incluye KPIs
        this.state = useState({
            // Filtros
            startDate: "",
            endDate: "",
            selectedVacancy: false,
            availableVacancies: [],
            sourceRecruitment: {},
            indicatorsSourceRecruitment: { sources: [] },
            rejectionReasons: { candidate: {}, company: {} },
            funnelRecruitment: {},
            requisitionStats: {},
            averageTimePerStageChart: {},
            averageTimePerStageCenterValue: "0 min",
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

    onKpisGridMounted(kpisGridComponent) {
        console.log("📊 Dashboard: KpisGrid montado", kpisGridComponent);
        this.kpisGridComponent = kpisGridComponent;
    }

    // ✅ NUEVO: Callback para RecruiterEfficiencyChart
    onRecruiterEfficiencyMounted(recruiterEfficiencyComponent) {
        console.log("📊 Dashboard: RecruiterEfficiencyChart montado", recruiterEfficiencyComponent);
        this.recruiterEfficiencyComponent = recruiterEfficiencyComponent;
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
        console.log("📅 Dashboard: Cambio de fechas:", { startDate, endDate });
        
        this.state.startDate = startDate;
        this.state.endDate = endDate;
        
        // ✅ Notificar al KpisGrid del cambio usando la referencia guardada
        if (this.kpisGridComponent) {
            console.log("🔄 Dashboard: Recargando KPIs...");
            await this.kpisGridComponent.loadKpisData();
        }

        // ✅ NUEVO: Notificar al RecruiterEfficiencyChart
        if (this.recruiterEfficiencyComponent) {
            console.log("🔄 Dashboard: Recargando gráfico de eficiencia...");
            await this.recruiterEfficiencyComponent.loadChartData();
        }
        
        // Recargar datos de gráficos
        await this.loadAllData();
    }

    async loadAllData() {
        try {
            await Promise.all([
                this.getAllVacancies(),
                // this.getTopRecruitments(),
                this.getSourceRecruitment(),
                this.getIndicatorsSourceRecruitment(),
                this.getRejectionReasons(),
                this.getVacancyMetrics(),
                this.getFunnelRecruitment(),
                this.getRequisitionStats(),
                this.getAverageTimePerStage(),
            ]);
            console.log("✅ Dashboard: Todos los datos cargados");
        } catch (error) {
            console.error("❌ Dashboard: Error cargando datos:", error);
        }
    }

    async getAllVacancies() {
        const jobs = await this.orm.searchRead('hr.job', [], ['id','name']);
        this.state.vacancyOptions = jobs.map(j => ({
            id: j.id,
            name: j.name,
        }));

        this.state.filteredVacancyOptions = this.state.vacancyOptions;
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

        // 10) Labels, colores, opciones
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
                            const n = counts[ctx.dataIndex];
                            const total = counts[0] || 1;
                            const pct = ((n / total) * 100).toFixed(1);
                            return `${labels[ctx.dataIndex]}: ${n} (${pct}%)`;
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
                        const n = counts[ctx.dataIndex];
                        const total = counts[0] || 1;
                        const pct = ((n / total) * 100).toFixed(0);
                        return `${labels[ctx.dataIndex]}\n${n}\n${pct}%`;
                    }
                }
            }
        };

        // 11) Actualizar estado
        this.state.funnelRecruitment = {
            data: { 
                labels, 
                datasets: [{ 
                    data: counts, 
                    backgroundColor: colors 
                }] 
            },
            options,
            enableDataLabels: true
        };

    }

    async getTopRecruitments() {
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

        // 6. Preparar datos para ApexCharts - Barras apiladas
        const labels = recruiterStats.map(r => r.name);
        const ongoingCounts = recruiterStats.map(r => r.ongoing);
        const hiredCounts = recruiterStats.map(r => r.hired);

        // ✅ BARRAS APILADAS como el ejemplo
        this.state.topRecruitments = {
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
            categories: labels,  // Nombres de los reclutadores
            colors: ['#80c7fd', '#00E396'],  // Azul claro y verde como el ejemplo
            meta: recruiterStats,  // Para los clicks
            filename: 'eficiencia_reclutadores',  // Para descargas
            options: {
                chart: {
                    type: 'bar',
                    stacked: true,
                    events: {
                        dataPointSelection: (event, chartContext, config) => {
                            const seriesIndex = config.seriesIndex;  // 0 = En Proceso, 1 = Contratados
                            const dataPointIndex = config.dataPointIndex;  // Índice del reclutador
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
                        horizontal: true  // ✅ Barras horizontales como el ejemplo
                    }
                },
                dataLabels: {
                    enabled: true,  // ✅ Habilitar labels dentro de las barras
                    formatter: function (val) {
                        return val > 0 ? val : '';  // Solo mostrar si hay valor
                    },
                    style: {
                        colors: ['#fff'],  // Texto blanco para contraste
                        fontSize: '12px',
                        fontWeight: 'bold'
                    }
                },
                stroke: {
                    width: 1,
                    colors: ['#fff']
                },
                title: {
                    text: 'Eficiencia de Contratación por Reclutador',
                    align: 'center',
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }
                },
                xaxis: {
                    categories: labels,
                    labels: {
                        show: false  // ✅ Ocultar labels del eje X (los nombres irán en dataLabels)
                    }
                },
                yaxis: {
                    labels: {
                        show: true  // ✅ Mostrar nombres de reclutadores en el eje Y
                    }
                },
                legend: {
                    position: 'top',  // Como el ejemplo
                    horizontalAlign: 'left'  // Como el ejemplo
                },
                fill: {
                    opacity: 1
                },
                tooltip: {
                    shared: true,  // Muestra ambas series en el tooltip
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

        // Forzar refresco del estado
        this.state.topRecruitments = { ...this.state.topRecruitments };

        console.log("📊 Datos ApexCharts - Barras Apiladas:", this.state.topRecruitments);
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
                onClick: (event, activeElements) => {
                    if (!activeElements.length) return;
                    const { index } = activeElements[0];
                    const src = this.state.sourceRecruitment.meta[index];
                    this.openSourceRecruitmentList(src.sourceId);
                },
                plugins: {
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
    }

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
    }

    async getRejectionReasons() {
        const context = { context: { active_test: false } };
        let domain = [["application_status", "=", "refused"]];
        domain = this._addDateRangeToDomain(domain);

        // Agrupa por motivo de rechazo
        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["refuse_reason_id"],
            ["refuse_reason_id"],
            context
        );

        // Separa en declinaciones de candidatos y rechazos de empresa
        const candidateDeclines = [];
        const companyRejections = [];

        for (const r of data) {
            const id = r.refuse_reason_id && r.refuse_reason_id[0] || false;
            const label = (r.refuse_reason_id && r.refuse_reason_id[1]) || "Sin motivo";
            const count = r.refuse_reason_id_count;

            if (label.toLowerCase().includes("declino")) {
                candidateDeclines.push({ id, label, count });
            } else {
                companyRejections.push({ id, label, count });
            }
        }

        // Datos para ChartRenderer
        const pastelCandidate = this.getPastelColors(candidateDeclines.length);
        const pastelCompany = this.getPastelColors(companyRejections.length);

        // Calcula el total de cada grupo para el porcentaje
        const totalCandidate = candidateDeclines.reduce((sum, x) => sum + x.count, 0);
        const totalCompany = companyRejections.reduce((sum, x) => sum + x.count, 0);

        this.state.rejectionReasons.candidate = {
            data: {
                labels: candidateDeclines.map(x => x.label),
                datasets: [{
                    label: "Declinaciones Candidatos",
                    data: candidateDeclines.map(x => x.count),
                    backgroundColor: pastelCandidate
                }]
            },  
            meta: candidateDeclines,          
            options: {              
                onClick: (event, activeElements, chart) => {
                    if (!activeElements.length) return;
                    const { index } = activeElements[0];
                    const reason = this.state.rejectionReasons.candidate.meta[index];
                    this.openRejectionList(reason.id);
                },  
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterBody: (context) => {
                                const idx = context[0].dataIndex;
                                const count = candidateDeclines[idx].count;
                                const percent = totalCandidate > 0 ? ((count / totalCandidate) * 100).toFixed(2) : "0.00";
                                return `Porcentaje de rechazo: ${percent}%`;
                            }
                        }
                    }
                }
            } 
        };

        this.state.rejectionReasons.company = {
            data: {
                labels: companyRejections.map(x => x.label),
                datasets: [{
                    label: "Rechazos Empresa",
                    data: companyRejections.map(x => x.count),
                    backgroundColor: pastelCompany
                }]
            },
            meta: companyRejections,
            options: {
                onClick: (event, activeElements, chart) => {
                    if (!activeElements.length) return;
                    const { index } = activeElements[0];
                    const reason = this.state.rejectionReasons.company.meta[index];
                    this.openRejectionList(reason.id);
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterBody: (context) => {
                                const idx = context[0].dataIndex;
                                const count = companyRejections[idx].count;
                                const percent = totalCompany > 0 ? ((count / totalCompany) * 100).toFixed(2) : "0.00";
                                return `Porcentaje de rechazo: ${percent}%`;
                            }
                        }
                    }
                }
            }
        };

        // Forzar refresco
        this.state.rejectionReasons = { ...this.state.rejectionReasons };
    }

    async getAverageTimePerStage() {
        console.log("📊 Calculando tiempo promedio por etapa (solo contratados)...");
        
        // 1) Obtener applicants contratados en el rango de fechas
        let hiredDomain = [["application_status", "=", "hired"]];
        hiredDomain = this._getHiredDateRangeDomain(hiredDomain);
        
        const hiredApplicants = await this.orm.searchRead(
            "hr.applicant",
            hiredDomain,
            ["id"]
        );
        
        console.log("👥 Applicants contratados encontrados:", hiredApplicants.length);
        
        if (hiredApplicants.length === 0) {
            console.log("⚠️ No hay contratados en este rango, manteniendo valores por defecto");
            return;
        }
        
        // 2) Obtener IDs de los applicants contratados
        const hiredIds = hiredApplicants.map(a => a.id);
        
        // 3) Consultar historial con duración en horas también
        const historyRecords = await this.orm.searchRead(
            "hr.applicant.stage.history",
            [
                ['applicant_id', 'in', hiredIds],
                ['leave_date', '!=', false],
                ['duration_hours', '>', 0]
            ],
            ['stage_id', 'duration_days', 'duration_hours', 'applicant_id']
        );
        
        console.log("📈 Registros de historial de contratados:", historyRecords.length);
        console.log("📊 Detalle de registros:", historyRecords);
        
        // 4) Agrupar por etapa
        const stageTimeMap = {};
        
        for (const record of historyRecords) {
            const stageId = record.stage_id[0];
            const stageName = record.stage_id[1];
            
            if (!stageTimeMap[stageId]) {
                stageTimeMap[stageId] = {
                    name: stageName,
                    durations: []
                };
            }
            
            stageTimeMap[stageId].durations.push({
                days: record.duration_days,
                hours: record.duration_hours
            });
        }
        
        // 5) Calcular promedios
        const labels = [];
        const data = [];
        let totalHours = 0;
        let totalCount = 0;
        
        for (const stageId in stageTimeMap) {
            const stage = stageTimeMap[stageId];
            const durations = stage.durations;
            
            if (durations.length > 0) {
                const avgHours = durations.reduce((sum, d) => sum + d.hours, 0) / durations.length;
                const avgDays = avgHours / 24;
                
                labels.push(stage.name);
                data.push(Number(avgDays.toFixed(2)));
                
                totalHours += avgHours * durations.length;
                totalCount += durations.length;
                
                console.log(`📋 ${stage.name}: ${avgDays.toFixed(2)} días promedio (${durations.length} muestras)`);
            }
        }
        
        // 6) Si no hay datos válidos, usar datos de prueba
        if (labels.length === 0) {
            console.log("⚠️ No hay datos válidos, usando datos de prueba");
            labels.push("Primera Entrevista", "Examen Técnico", "Examen Médico");
            data.push(0.1, 0.2, 0.05);
            totalHours = 4.8;
            totalCount = 3;
        }
        
        // 7) Formatear el promedio global
        const globalAverageHours = totalCount > 0 ? (totalHours / totalCount) : 0;
        let centerText = "0 min";
        
        if (globalAverageHours >= 24) {
            const days = (globalAverageHours / 24).toFixed(1);
            centerText = `${days} día${days != 1 ? 's' : ''}`;
        } else if (globalAverageHours >= 1) {
            const hours = globalAverageHours.toFixed(1);
            centerText = `${hours} hora${hours != 1 ? 's' : ''}`;
        } else if (globalAverageHours > 0) {
            const minutes = Math.round(globalAverageHours * 60);
            centerText = `${minutes} min`;
        }
        
        // 8) ¡CLAVE! Crear un NUEVO objeto para forzar reactivity en OWL
        this.state.averageTimePerStageChart = {
            data: {
                labels,
                datasets: [{
                    data,
                    backgroundColor: this.getPastelColors(labels.length),
                }]
            },
            options: {
                cutout: "70%",
                plugins: {
                    legend: { display: true, position: "bottom" },
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const days = ctx.parsed;
                                const hours = (days * 24);
                                
                                let timeText = "";
                                if (days >= 1) {
                                    timeText = `${days.toFixed(1)} días`;
                                } else if (hours >= 1) {
                                    timeText = `${hours.toFixed(1)} horas`;
                                } else {
                                    const minutes = Math.round(hours * 60);
                                    timeText = `${minutes} minutos`;
                                }
                                
                                return [
                                    `${ctx.label}: ${timeText}`,
                                    `(Solo candidatos contratados)`
                                ];
                            }
                        }
                    }
                }
            }
        };
        
        this.state.averageTimePerStageCenterValue = centerText;
        
        // 9) ¡SÚPER IMPORTANTE! Forzar actualización completa del estado
        this.state.averageTimePerStageChart = { ...this.state.averageTimePerStageChart };
        
        console.log("✅ Gráfica actualizada - Promedio global:", centerText);
        console.log("🎯 Basado en", hiredApplicants.length, "candidatos contratados");
        console.log("📊 Chart data:", this.state.averageTimePerStageChart);
    }

    openRejectionList(refuse_reason_id) {
        let domain = [
            ["application_status", "=", "refused"],            
        ];

        if (refuse_reason_id === false){
            domain.push(["refuse_reason_id", "=", false]);
        } else if (refuse_reason_id){
            domain.push(["refuse_reason_id", "=", refuse_reason_id]);
        }else {
            domain.push("|", 
                   ["refuse_reason_id", "=", false],
                   ["refuse_reason_id", "=", null]);
        }
    
        domain = this._addDateRangeToDomain(domain);

        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Solicitudes Rechazadas',
            res_model: 'hr.applicant',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            domain: domain,
            context: {
                search_default_filter_refused: 1,
                active_test: false
            }
        });
    }

}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = {
    DashboardHeader, KpisGrid, 
    ChartRenderer, RecruiterEfficiencyChart
};

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);