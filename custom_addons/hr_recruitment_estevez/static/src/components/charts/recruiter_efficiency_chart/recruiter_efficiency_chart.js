/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class RecruiterEfficiencyChart extends Component {

    static template = "hr_recruitment_estevez.RecruiterEfficiencyChart";
    static components = { ChartRendererApex };
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

        // ✅ Local state for chart data
        this.state = useState({
            chartData: {
                series: [],
                categories: [],
                colors: ['#FFD700', '#00E396', '#3f51b5'],
                meta: [],
                filename: 'recruiter_efficiency_post_first_interview',
                options: {}
            },
            isLoading: true
        });

        // ✅ Load data on initialization
        onWillStart(async () => {
            await this.loadChartData();
        });

        // ✅ Notify parent component when mounted
        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });
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

    _getHiredDateRangeDomain(domain = []) {
        if (this.props.startDate) {
            domain.push(["date_closed", ">=", this.props.startDate]);
        }
        if (this.props.endDate) {
            domain.push(["date_closed", "<=", this.props.endDate]);
        }
        return domain;
    }

    async loadChartData() {
        this.state.isLoading = true;

        try {
            await this.calculateRecruiterStats();
        } catch (error) {
            console.error("❌ RecruiterEfficiencyChart: Error loading data:", error);
            this._setEmptyChartData();
        } finally {
            this.state.isLoading = false;
        }
    }

    async calculateRecruiterStats() {
        try {
            // ✅ STEP 1: Use service to get First Interview stage
            const firstInterviewStage = await this.recruitmentStageService.getFirstInterviewStage();
            
            if (!firstInterviewStage) {
                console.error("❌ RecruiterEfficiencyChart: 'First Interview' stage NOT found");
                this._setEmptyChartData();
                return;
            }

            // ✅ STEP 2: TOTAL - Post primera entrevista
            const totalStats = await this._calculateTotalPostFirstInterview();
            
            // ✅ STEP 3: ONGOING - Created in range + Post-First Interview + Ongoing
            const ongoingStats = await this._calculateOngoingPostFirstInterview();
            
            // ✅ STEP 4: HIRED - Hired in range + Post-First Interview
            const hiredStats = await this._calculateHiredPostFirstInterview();

            const hiredInRangeButCreatedBeforeStats = await this._calculateHiredInRangeButCreatedBefore();

            const rejectedStats = await this._calculateRejectedPostFirstInterview();

            // ✅ STEP 5: Consolidate data by recruiter
            const recruiterStats = this._consolidateRecruiterStats(
                totalStats, ongoingStats, hiredStats, rejectedStats, 
                hiredInRangeButCreatedBeforeStats
            );

            // ✅ STEP 6: Build chart
            this._buildChartData(recruiterStats);

        } catch (error) {
            console.error("❌ RecruiterEfficiencyChart: Error calculating stats:", error);
            this._setEmptyChartData();
        }
    }

    // ✅ HELPER METHOD: Total candidates created in range that reached post-First Interview
    async _calculateTotalPostFirstInterview() {
        const baseDomain = this._addDateRangeToDomain([]);
        const domain = await this.recruitmentStageService.getPostFirstInterviewDomain(baseDomain, true);

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        return data;
    }

    // ✅ HELPER METHOD: Ongoing post-First Interview
    async _calculateOngoingPostFirstInterview() {
        const baseDomain = [
            ...this._addDateRangeToDomain([]),
            ["application_status", "=", "ongoing"]
        ];
        const domain = await this.recruitmentStageService.getPostFirstInterviewDomain(baseDomain, false);

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        console.log("📊 Ongoing post-First Interview:", data.length);
        return data;
    }

    // ✅ HELPER METHOD: Hired post-First Interview
    async _calculateHiredPostFirstInterview() {
        const baseDomain = [
            ...this._addDateRangeToDomain([]),  // ✅ Filter by CREATION date
            ["application_status", "=", "hired"]
        ];
        const domain = await this.recruitmentStageService.getPostFirstInterviewDomain(baseDomain, false);

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        console.log("📊 Hired post-First Interview:", data.length);
        return data;
    }

    async _calculateRejectedPostFirstInterview() {
        const baseDomain = [
            ...this._addDateRangeToDomain([]),  // ✅ Filter by CREATION date
            ["application_status", "=", "refused"]
        ];
        const domain = await this.recruitmentStageService.getPostFirstInterviewDomain(baseDomain, false);

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"],
            { context: { active_test: false } }
        );

        console.log("📊 Rejected post-First Interview:", data.length);
        return data;
    }

    // ✅ HELPER METHOD: Consolidate statistics by recruiter
    _consolidateRecruiterStats(totalStats, ongoingStats, hiredStats, rejectedStats, hiredInRangeButCreatedBeforeStats) {
        const recruiterMap = {};

        // Initialize with totals (SOLO creados en rango)
        for (const stat of totalStats) {
            const id = (stat.user_id && stat.user_id[0]) || false;
            const name = (stat.user_id && stat.user_id[1]) || "Unassigned";
            recruiterMap[id] = {
                id,
                name,
                total: stat.user_id_count,  // ✅ SOLO candidatos creados en rango
                hired: 0,
                hiredSecondary: 0,  // ✅ Solo para información en tooltip
                ongoing: 0,
                rejected: 0
            };
        }

        // Add hired (creados en rango)
        for (const stat of hiredStats) {
            const id = (stat.user_id && stat.user_id[0]) || false;
            if (recruiterMap[id]) {
                recruiterMap[id].hired = stat.user_id_count;
            }
        }

        // ✅ Add hired secondary (SOLO para tooltip, NO afecta total)
        for (const stat of hiredInRangeButCreatedBeforeStats) {
            const id = (stat.user_id && stat.user_id[0]) || false;
            
            // ✅ Solo agregar hiredSecondary si el reclutador ya existe
            if (recruiterMap[id]) {
                recruiterMap[id].hiredSecondary = stat.user_id_count;
            } else {
                // ✅ Si no existe, crear entrada SOLO para hiredSecondary (total = 0)
                const name = (stat.user_id && stat.user_id[1]) || "Unassigned";
                recruiterMap[id] = {
                    id,
                    name,
                    total: 0,  // ✅ NO cuenta en el total de barras
                    hired: 0,
                    hiredSecondary: stat.user_id_count,  // ✅ Solo información
                    ongoing: 0,
                    rejected: 0
                };
            }
        }

        // Add ongoing
        for (const stat of ongoingStats) {
            const id = (stat.user_id && stat.user_id[0]) || false;
            if (recruiterMap[id]) {
                recruiterMap[id].ongoing = stat.user_id_count;
            }
        }

        // Add rejected
        for (const stat of rejectedStats) {
            const id = (stat.user_id && stat.user_id[0]) || false;
            if (recruiterMap[id]) {
                recruiterMap[id].rejected = stat.user_id_count;
            }
        }

        // Calculate percentages and sort
        const recruiterStats = Object.values(recruiterMap)
            .map(r => ({
                ...r,
                totalHired: r.hired + r.hiredSecondary,  // ✅ Para información en tooltip
                percentage: r.total > 0 ? ((r.hired / r.total) * 100).toFixed(2) : "0.00"
            }))
            .filter(r => r.total > 0 || r.hiredSecondary > 0)  // ✅ Mostrar si tiene total O hiredSecondary
            .sort((a, b) => b.total - a.total);  // ✅ Ordenar SOLO por total (creados en rango)

        console.log("📊 Consolidated stats by recruiter (total excludes hiredSecondary):", recruiterStats);
        return recruiterStats;
    }

    async _calculateHiredInRangeButCreatedBefore() {
        if (!this.props.startDate || !this.props.endDate) {
            return [];
        }

        const baseDomain = [
            ["application_status", "=", "hired"],
            ["date_closed", ">=", this.props.startDate],     // ✅ Contratado en el rango
            ["date_closed", "<=", this.props.endDate],       // ✅ Contratado en el rango
            ["create_date", "<", this.props.startDate]       // ✅ Creado ANTES del rango
        ];
        
        const domain = await this.recruitmentStageService.getPostFirstInterviewDomain(baseDomain, false);

        const data = await this.orm.readGroup(
            "hr.applicant",
            domain,
            ["user_id"],
            ["user_id"]
        );

        return data;
    }

    // ✅ HELPER METHOD: Build chart data
    _buildChartData(recruiterStats) {
        const labels = recruiterStats.map(r => r.name);
        const totalCounts = recruiterStats.map(r => r.total);
        const ongoingCounts = recruiterStats.map(r => r.ongoing);
        const hiredCounts = recruiterStats.map(r => r.hired);

        this.state.chartData = {
            series: [
                {
                    name: 'Total (Superaron la Primera Entrevista)',
                    data: totalCounts,
                    stack: 'total'
                },
                {
                    name: 'En Proceso',
                    data: ongoingCounts,
                    stack: 'detail'
                },
                {
                    name: 'Contratados',
                    data: hiredCounts,
                    stack: 'detail'
                }
            ],
            categories: labels,
            colors: ['#FFD700', '#00E396', '#3f51b5'],
            meta: recruiterStats,
            filename: 'recruiter_efficiency_post_first_interview',
            options: this._getChartOptions(labels, recruiterStats)
        };
    }

    // ✅ HELPER METHOD: Chart configuration
    _getChartOptions(labels, recruiterStats) {
        return {
            chart: {
                type: 'bar',
                stacked: true,
                height: this.props.height || 400,
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        const seriesIndex = config.seriesIndex;
                        const dataPointIndex = config.dataPointIndex;
                        const stat = recruiterStats[dataPointIndex];

                        let onlyHired = false;
                        let onlyOngoing = false;
                        let showAll = false;

                        if (seriesIndex === 0) {         // Total
                            showAll = true;
                        } else if (seriesIndex === 1) {  // Ongoing
                            onlyOngoing = true;
                        } else if (seriesIndex === 2) {  // Hired
                            onlyHired = true;
                        }

                        this.openRecruitmentList(stat.id, onlyHired, onlyOngoing, showAll);
                    }
                }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    barHeight: '50%',
                    distributed: false,
                    dataLabels: {
                        position: 'center'
                    }
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                width: 1,
                colors: ['#fff']
            },
            title: {
                text: this.props.title || 'Recruiter Hiring Efficiency (Post-First Interview)',
                align: 'center',
                style: {
                    fontSize: '16px',
                    fontWeight: 'bold'
                }
            },
            xaxis: {
                categories: labels,
                labels: {
                    show: false
                }
            },
            yaxis: {
                labels: {
                    show: true
                }
            },
            legend: {
                position: 'top',
                horizontalAlign: 'left',
                markers: {
                    width: 12,
                    height: 12,
                    strokeWidth: 0,
                    strokeColor: '#fff',
                    fillColors: undefined,
                    radius: 12,
                    customHTML: undefined,
                    onClick: undefined,
                    offsetX: 0,
                    offsetY: 0
                }
            },
            fill: {
                opacity: [0.9, 1, 1]
            },
            grid: {
                show: true,
                borderColor: '#f1f1f1',
                strokeDashArray: 0,
                position: 'back',
                xaxis: {
                    lines: {
                        show: true
                    }
                },
                yaxis: {
                    lines: {
                        show: false
                    }
                }
            },
            tooltip: {
                shared: false,
                intersect: true,
                fixed: {
                    enabled: true,
                    position: 'topRight',
                    offsetX: -50,
                    offsetY: 0,
                },
                followCursor: false,
                theme: 'light',
                style: {
                    fontSize: '12px',
                    fontFamily: undefined
                },
                custom: function ({ series, seriesIndex, dataPointIndex, w }) {
                    const stat = recruiterStats[dataPointIndex];
                    const value = series[seriesIndex][dataPointIndex];

                    let content = '';
                    if (seriesIndex === 0) {
                        // Total
                        content = `
                            <div class="px-3 py-2">
                                <div class="fw-bold">${stat.name}</div>
                                <div class="text-muted">Candidatos que superaron la Primera Entrevista</div>
                                <div class="small fw-bold">
                                    <span style="color: #2238b3ff;">Total: ${value}</span> | 
                                    <span style="color: #00E396;">En Proceso: ${stat.ongoing}</span> | 
                                    <span style="color: #FF8C00;">Contratados: ${stat.hired}</span> | 
                                    <span class="text-danger">Rechazados: ${stat.rejected}</span>
                                </div>
                                ${stat.hiredSecondary > 0 ? `
                                    <div class="small fw-bold mb-2" style="color: #FF8C00;">
                                        Contratados (Creados Antes del Rango): ${stat.hiredSecondary}
                                    </div>
                                ` : ''}
                                <hr class="my-1">
                                <div class="small">Tasa de conversión: ${stat.percentage}%</div>
                            </div>`;
                    } else if (seriesIndex === 1) {
                        // Ongoing
                        content = `
                            <div class="px-3 py-2">
                                <div class="fw-bold">${stat.name}</div>
                                <div class="text-muted">Candidatos que superaron la Primera Entrevista y siguen en proceso</div>
                                <div class="fw-bold text-success">En proceso: <span>${value}</span></div>
                            </div>`;
                    } else if (seriesIndex === 2) {
                        // Hired
                        content = `
                            <div class="px-3 py-2">
                                <div class="fw-bold">${stat.name}</div>
                                <div class="text-muted">Candidatos que superaron la Primera Entrevista y fueron contratados</div>
                                <div class="fw-bold" style="color: #FF8C00;">Contratados: <span>${value}</span></div>
                                ${stat.hiredSecondary > 0 ? `
                                    <div class="small fw-bold mb-2" style="color: #FF8C00;">
                                        Contratados (Creados Antes del Rango): ${stat.hiredSecondary}
                                    </div>
                                ` : ''}
                                <hr class="my-1">
                                <div class="text-muted">Tasa de conversión: ${stat.percentage}%</div>
                            </div>`;
                    }

                    return content;
                }
            }
        };
    }

    // ✅ HELPER METHOD: Empty chart data
    _setEmptyChartData() {
        this.state.chartData = {
            series: [],
            categories: [],
            colors: ['#FFD700', '#00E396', '#3f51b5'],
            meta: [],
            filename: 'recruiter_efficiency_post_first_interview',
            options: {}
        };
    }

    // ✅ Navigation to applications list
    async openRecruitmentList(userId, onlyHired = false, onlyOngoing = false, showAll = false) {
        try {
            // ✅ Base domain for post-First Interview
            const baseDomain = [
                ...this._addDateRangeToDomain([]),
                ["user_id", "=", userId]
            ];
            
            const domain = await this.recruitmentStageService.getPostFirstInterviewDomain(baseDomain, showAll);

            // ✅ Filter by specific type if not "showAll"
            if (!showAll) {
                if (onlyHired) {
                    domain.push(["application_status", "=", "hired"]);
                } else if (onlyOngoing) {
                    domain.push(["application_status", "=", "ongoing"]);
                }
            }

            // ✅ Determine action name
            let actionName = 'All Applications (Post-First Interview)';
            if (onlyHired) {
                actionName = 'Hired (Post-First Interview)';
            } else if (onlyOngoing) {
                actionName = 'Ongoing (Post-First Interview)';
            }

            await this.actionService.doAction({
                type: 'ir.actions.act_window',
                name: actionName,
                res_model: 'hr.applicant',
                views: [[false, 'list'], [false, 'form']],
                domain: domain,
                context: { active_test: false },
            });

        } catch (error) {
            console.error("❌ RecruiterEfficiencyChart: Error in navigation:", error);
        }
    }
}