/** @odoo-module **/

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card/kpi_card";
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

    setup() {
        const now = DateTime.now();
        const startOfMonth = now.startOf('month').toISODate();
        const endOfMonth = now.endOf('month').toISODate();

        this.state = useState({
            // Postulaciones Totales
            totalApplicants: {
                value: 0,
            },
            // Postulaciones En Progreso
            inProgressApplicants: {
                value: 0,
            },
            // Candidatos Preseleccionados
            preselectedApplicants: {
                value: 0,
            },
            // Postulaciones Rechazadas
            rejectedApplicants: {
                value: 0,
            },
            // Contrataciones Realizadas
            hiredApplicants: {
                value: 0,
            },
            // Tiempo promedio de contratación
            averageHiringTime: {
                value: 0,
            },
            // Postulaciones por Reclutador
            topRecruitments: {},
            // Fuentes de Reclutamiento
            sourceRecruitment: {},
            indicatorsSourceRecruitment: {
                sources: []
            },
            // Motivos de Rechazo
            rejectionReasons: {
                candidate: {},
                company: {},
            },
            // Embudo de Etaoas
            funnelRecruitment: {},

            //Vacante
            vacancyOptions: [],
            selectedVacancyId: false,
            vacancyMetrics: {
                status: '',
                openDuration: '',
                applicants: 0,
                hired: 0,
                refused: 0,
                topRefuseReason: '',
            },

            startDate: startOfMonth,
            endDate: endOfMonth,
        })

        this.orm = useService("orm");
        this.actionService = useService("action");

        onWillStart(async () => {
            // 1) cargar puestos
            const jobs = await this.orm.searchRead('hr.job', [], ['id','name']);
            this.state.vacancyOptions = jobs.map(j => ({
              id: j.id,
              name: j.name,
            }));
            // 2) resto de carga
            await this.loadAllData();
            this.getVacancyMetrics();
          });
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
    async openRecruitmentList(userId, onlyHired) {
        // 1) Arranca con el filtro de fecha
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
          ];
        domain = this._addDateRangeToDomain(domain);
    
        // 2) Filtra por reclutador y registro activo
        domain.push(["user_id", "=", userId]);
    
        // 3) Si venías del dataset de “Contratados”, añade también ese filtro
        if (onlyHired) {
          domain.push(["application_status", "=", "hired"]);
        }
    
        // 4) Lanza la acción con la lista de vistas
        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: onlyHired ? 'Contratados' : 'Postulaciones',
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

    onDateRangeChange() {
        if (this.state.startDate && this.state.endDate && this.state.endDate < this.state.startDate) {
            // Corrige automáticamente o muestra un mensaje
            this.state.endDate = this.state.startDate;
        }
        this.loadAllData();
        this.getVacancyMetrics();
    }

    async loadAllData() {        
        await Promise.all([
            this.getTopRecruitments(),
            this.getSourceRecruitment(),
            this.getIndicatorsSourceRecruitment(),
            this.getTotalApplicants(),
            this.getInProgressApplicants(),
            this.getPreselectedApplicants(),
            this.getRejectedApplicants(),
            this.getHiredApplicants(),
            this.getAverageHiringTime(),
            this.getRejectionReasons(),
            this.getFunnelRecruitment(),
            this.getRequisitionStats()
        ]);
    }

    getPastelColors(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = Math.floor((360 / count) * i + Math.random() * 30);
            colors.push(`hsl(${hue}, 70%, 85%)`);
        }
        return colors;
    }

    async getFunnelRecruitment() {
        // 1) Determinar jobId desde el select
        const rawJid = this.state.selectedVacancyId;
        const jobId  = rawJid && rawJid !== 'false' 
                     ? parseInt(rawJid, 10) 
                     : null;
    
        // 2) Cargar todas las etapas en orden
        const stages = await this.orm.searchRead(
            "hr.recruitment.stage",
            [],
            ["id", "name", "sequence"]
        );
        stages.sort((a, b) => a.sequence - b.sequence);
    
        // 3) Construir dominio: rango de fechas + job_id (si hay)
        let domain = this._addDateRangeToDomain([]);
        if (jobId) {
            domain.push(['job_id', '=', jobId]);
        }
    
        // 4) Leer grupo por etapa
        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["stage_id"],
            ["stage_id"]
        );
    
        // 5) Mapa etapa → conteo
        const stageCountMap = {};
        for (const r of data) {
            if (r.stage_id && r.stage_id[0]) {
                stageCountMap[r.stage_id[0]] = r.stage_id_count;
            }
        }
    
        // 6) Generar arrays
        const labels = stages.map(s => s.name);
        const counts = stages.map(s => stageCountMap[s.id] || 0);
        const colors = this.getPastelColors(labels.length);
    
        // 7) Opciones para mostrar % sobre el total de esta vacante
        const total = counts.reduce((a,b) => a+b, 0) || 1;
        const options = {
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const n = counts[ctx.dataIndex];
                            const pct = ((n/total)*100).toFixed(1);
                            return `${labels[ctx.dataIndex]}: ${n} candidatos (${pct}%)`;
                        }
                    }
                },
                datalabels: {
                    anchor: 'center',
                    align: 'center',
                    formatter: val => {
                        const pct = ((val/total)*100).toFixed(0);
                        return `${val}\n${pct}%`;
                    }
                }
            }
        };
    
        // 8) Actualizar el state
        this.state.funnelRecruitment = {
            data: { labels, datasets: [{ label: "Candidatos", data: counts, backgroundColor: colors }] },
            options
        };
    }

    async getTopRecruitments() {
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        domain = this._addDateRangeToDomain(domain);

        // Total postulaciones por reclutador
        const totalData = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        // Solo contratados por reclutador
        const hiredDomain = [
            ...domain,
            ["application_status", "=", "hired"]
        ];
        const hiredData = await this.orm.readGroup(
            "hr.applicant",
            hiredDomain,
            ["user_id"],
            ["user_id"]
        );

        const hiredMap = {};
        for (const r of hiredData) {
            const key = (r.user_id && r.user_id[1]) || "Desconocido";
            hiredMap[key] = r.user_id_count;
        }

        // Calcula porcentaje y prepara datos para tooltip
        const recruiterStats = totalData.map(r => {
            const id   = (r.user_id && r.user_id[0]) || false;
            const name = (r.user_id && r.user_id[1]) || "Desconocido";
            const total = r.user_id_count;
            const hired = hiredMap[name] || 0;
            const percentage = total > 0 ? ((hired / total) * 100).toFixed(2) : "0.00";
            return { id, name, total, hired, percentage };
        });

        // Si no hay datos, asegúrate de pasar arrays vacíos
        const labels = recruiterStats.length ? recruiterStats.map(r => r.name) : [];
        const totalCounts = recruiterStats.length ? recruiterStats.map(r => r.total) : [];
        const hiredCounts = recruiterStats.length ? recruiterStats.map(r => r.hired) : [];


        
        this.state.topRecruitments = {
            data: { labels, datasets: [
                { label: "Total Postulaciones", data: totalCounts, backgroundColor: "hsl(210,70%,85%)" },
                { label: "Contratados",          data: hiredCounts, backgroundColor: "hsl(140,70%,85%)" }
            ]},
            // lo guardamos aquí:
            meta: recruiterStats,
            options: {
                indexAxis: 'y',
                onClick: (event, activeElements, chart) => {
                    if (!activeElements.length) {
                      return;
                    }
                    const { datasetIndex, index } = activeElements[0];
                    const stat = this.state.topRecruitments.meta[index];
                    // si datasetIndex === 1 => contratados, else total
                    const onlyHired = datasetIndex === 1;
                    this.openRecruitmentList(stat.id, onlyHired);
                  },
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterBody: ctx => {
                                const stat = recruiterStats[ctx[0].dataIndex];
                                return `Porcentaje de contratación: ${stat.percentage}%`;
                            }
                        }
                    }
                }
            }
        };

        // Forzar refresco
        this.state.topRecruitments = { ...this.state.topRecruitments };
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
        const rawJid = this.state.selectedVacancyId;
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
            openDur = '—';
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
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];
        domain = this._addDateRangeToDomain(domain);
    
        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["source_id"],
            ["source_id"]
        );
    
        // Ahora guardamos el id junto con el label y el count:
        const sourcesData = data.map(r => ({
            sourceId:   r.source_id ? r.source_id[0] : null,
            label:      (r.source_id && r.source_id[1]) || "Sin fuente",
            count:      r.source_id_count,
        }));
    
        const labels = sourcesData.map(s => s.label);
        const counts = sourcesData.map(s => s.count);
        const colors = this.getPastelColors(labels.length);
    
        this.state.sourceRecruitment = {
            data: {
                labels,
                datasets: [{
                    label: "Fuentes de Postulación",
                    data: counts,
                    backgroundColor: colors,
                }]
            },
            // guardamos meta con el sourceId
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
                                return `${src.label}: ${src.count}`;
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
        let domain = [
            "|",
            ["active", "=", true],
            ["application_status", "=", "refused"]
        ];

        domain = this._addDateRangeToDomain(domain);

        // 1. Agrupa por source_id para obtener el total de candidatos por fuente
        const totalData = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["source_id"],
            ["source_id"]
        );

        // 2. Agrupa por source_id solo los contratados
        const hiredDomain = [
            ...domain,
            ["application_status", "=", "hired"]
        ];
        const hiredData = await this.orm.readGroup(
            "hr.applicant",
            hiredDomain,
            ["source_id"],
            ["source_id"]
        );

        // 3. Indexa los contratados por source_id para fácil acceso
        const hiredMap = {};
        for (const r of hiredData) {
            const key = (r.source_id && r.source_id[1]) || "Sin fuente";
            hiredMap[key] = r.source_id_count;
        }

        // 4. Construye el array de indicadores
        const indicators = totalData.map(r => {
            const label = (r.source_id && r.source_id[1]) || "Sin fuente";
            const total = r.source_id_count;
            const hired = hiredMap[label] || 0;
            const percentage = total > 0 ? ((hired / total) * 100).toFixed(2) : "0.00";
            return { label, total, hired, percentage };
        });

        // 5. Guarda en el estado
        this.state.indicatorsSourceRecruitment.sources = indicators;

    }

    async getTotalApplicants() {
        const context = { context: { active_test: false } };
        let domain = [];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.totalApplicants.value = data;
    }

    async getInProgressApplicants() {
        let domain = [["application_status", "=", "ongoing"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.inProgressApplicants.value = data;
    }

    async getPreselectedApplicants() {
        // Buscar applicants cuya etapa (stage_id.sequence) sea mayor a 4
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.preselectedApplicants.value = data;
    }

    async getRejectedApplicants() {
        const context = { context: { active_test: false } };
        let domain = [["application_status", "=", "refused"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain, context);
        this.state.rejectedApplicants.value = data;
    }

    async getHiredApplicants() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._addDateRangeToDomain(domain);

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.hiredApplicants.value = data;
    }

    async getAverageHiringTime() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._addDateRangeToDomain(domain);

        const applicants = await this.orm.searchRead('hr.applicant', domain, ["create_date", "date_closed"]);
        if (!applicants.length) {
            return 0;
        }

        let totalDays = 0;
        let count = 0;
        for (const applicant of applicants) {
            if (applicant.create_date && applicant.date_closed) {
                const created = new Date(applicant.create_date);
                const closed = new Date(applicant.date_closed);
                const diffTime = closed - created;
                const diffDays = diffTime / (1000 * 60 * 60 * 24);
                totalDays += diffDays;
                count += 1;
            }
        }

        const averageDays = count ? (totalDays / count) : 0;
        this.state.averageHiringTime.value = averageDays.toFixed(2);
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

    viewTotalApplicants() {
        const context = { active_test: false };
        let domain = [];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: context,
        });
    }

    viewInProgressApplicants() {
        let domain = [["application_status", "=", "ongoing"]];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones en Progreso",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
        });
    }

    viewPreselectedApplicants() {
        let domain = [
            ["stage_id.sequence", ">", 4],
            ["application_status", "!=", "hired"]
        ];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones Preseleccionadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
        });
    }

    viewRejectedApplicants() {
        const context = { active_test: false };
        let domain = [["application_status", "=", "refused"]];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones Rechazadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            context: context
        });
    }

    viewHiredApplicants() {
        let domain = [["application_status", "=", "hired"]];
        domain = this._addDateRangeToDomain(domain);

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Postulaciones Contratadas",
            res_model: "hr.applicant",
            domain: domain,
            views: [[false, "list"], [false, "form"]]
        });
    }

    viewAverageHiringTime() {
        // No-op to avoid errors
        return;
    }

}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = { KpiCard, ChartRenderer };

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);