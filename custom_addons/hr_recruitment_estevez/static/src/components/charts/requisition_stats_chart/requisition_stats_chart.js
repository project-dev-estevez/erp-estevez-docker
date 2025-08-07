/** @odoo-module */

import { Component, useState, onWillStart, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class RequisitionStatsChart extends Component {
    static template = "hr_recruitment_estevez.RequisitionStatsChart";
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

        this.state = useState({
            apexConfig: {
                series: [],
                options: {}
            },
            chartKey: 'requisition-stats-' + Date.now(),
            isLoading: true,
            hasData: false,
            requisitionData: {}
        });

        onWillStart(async () => {
            await this.loadChartData();
        });

        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });

        onWillUpdateProps(async (nextProps) => {
            if (this.props.startDate !== nextProps.startDate || 
                this.props.endDate !== nextProps.endDate) {
                
                console.log("📅 RequisitionStatsChart: Fechas cambiaron, recargando...");
                this.tempProps = nextProps;
                await this.loadChartData();
                this.tempProps = null;
            }
        });
    }

    getCurrentProps() {
        return this.tempProps || this.props;
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

    async loadChartData() {
        console.log("📊 RequisitionStatsChart: Cargando datos de requisiciones...");
        
        this.state.isLoading = true;

        try {
            await this.getRequisitionStats();
            console.log("✅ RequisitionStatsChart: Datos cargados correctamente");
        } catch (error) {
            console.error("❌ RequisitionStatsChart: Error cargando datos:", error);
            this.showEmptyChart();
        } finally {
            this.state.isLoading = false;
        }
    }

    async getRequisitionStats() {
        let domain = [];

        const data = await this.orm.readGroup(
            'hr.requisition',
            domain,
            ['state'],
            ['state']
        );

        // Convertir a un map
        const countMap = {};
        data.forEach(r => {
            countMap[r.state] = r.state_count;
        });

        // ✅ Definir labels con la nueva barra "Por Aprobar"
        const labels = [
            'Total',
            'Por Aprobar',  // to_approve (nueva barra)
            'Por Abrir',    // first_approval + approved no publicadas
            'Abiertas',     // approved & is_published = true
            'Cerradas'      // approved & is_published = false (pero que ya estuvieron abiertas)
        ];

        // Total = suma de todos
        const total = data.reduce((sum, r) => sum + r.state_count, 0);

        // ✅ Por Aprobar = solo to_approve
        const countToApprove = countMap['to_approve'] || 0;

        // ✅ Por Abrir = first_approval + approved no publicadas
        const countFirstApproval = countMap['first_approval'] || 0;
        const countApprovedNotPublished = await this.orm.searchCount(
            'hr.requisition',
            [...domain, ['state', '=', 'approved'], ['is_published', '=', false], ['close_date', '=', false]]
        );
        const countPorAbrir = countFirstApproval + countApprovedNotPublished;
        
        const countApprovedOpen = await this.orm.searchCount(
            'hr.requisition',
            [...domain, ['state', '=', 'approved'], ['is_published', '=', true]]
        );
        
        // ✅ Cerradas = las que estuvieron abiertas pero ya se cerraron (tienen close_date)
        const countApprovedClosed = await this.orm.searchCount(
            'hr.requisition',
            [...domain, ['state', '=', 'approved'], ['is_published', '=', false], ['close_date', '!=', false]]
        );

        const counts = [
            total,
            countToApprove,     // Nueva barra
            countPorAbrir,      // Renombrada para claridad
            countApprovedOpen,
            countApprovedClosed,
        ];

        const colors = this.getPastelColors(labels.length);

        // ✅ Crear metadata para el click (con nueva barra)
        const meta = [
            { state: null },                // para "Total"
            { state: 'to_approve' },        // nueva barra "Por Aprobar"
            { state: 'por_abrir' },         // código especial para "Por Abrir"
            { state: 'approved_open' },     
            { state: 'approved_closed' },
        ];

        // ✅ Configurar ApexChart
        this.state.chartKey = 'requisition-stats-' + Date.now();
        
        this.state.apexConfig = {
            series: [{
                name: "Requisiciones",
                data: counts
            }],
            options: {
                title: {
                    text: this.props.title || 'Requisiciones por Estado',
                    align: 'center',
                    style: {
                        fontSize: '16px',
                        fontWeight: 'bold',
                        color: '#495057'
                    }
                },
                chart: {
                    type: 'bar',
                    height: this.props.height || 400,
                    id: 'requisition-stats-' + Date.now(),
                    events: {
                        dataPointSelection: (event, chartContext, config) => {
                            const item = meta[config.dataPointIndex];
                            this.openRequisitionList(item.state);
                        }
                    }
                },
                plotOptions: {
                    bar: {
                        borderRadius: 6,
                        horizontal: false,
                        columnWidth: '60%',
                        dataLabels: {
                            position: 'top'
                        }
                    }
                },
                colors: colors,
                dataLabels: {
                    enabled: false,
                    formatter: function (val) {
                        return val > 0 ? val : '';
                    },
                    style: {
                        fontSize: '12px',
                        fontWeight: 'bold',
                        colors: ['#333']
                    },
                    offsetY: -20
                },
                xaxis: {
                    categories: labels,
                    labels: {
                        style: {
                            fontSize: '12px',
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
                            const label = labels[dataPointIndex];
                            return `<strong>${label}</strong><br/>${value} requisiciones<br/><em>Haz clic para ver detalles</em>`;
                        }
                    },
                    theme: 'dark'
                },
                grid: {
                    show: true,
                    borderColor: '#f1f1f1',
                    strokeDashArray: 3,
                    yaxis: {
                        lines: { show: true }
                    },
                    xaxis: {
                        lines: { show: false }
                    }
                },
                responsive: [{
                    breakpoint: 768,
                    options: {
                        plotOptions: {
                            bar: {
                                columnWidth: '80%'
                            }
                        },
                        dataLabels: {
                            style: {
                                fontSize: '10px'
                            }
                        }
                    }
                }]
            }
        };

        this.state.requisitionData = {
            total,
            countToApprove,
            countPorAbrir,
            countApprovedOpen,
            countApprovedClosed,
            meta
        };

        this.state.hasData = total > 0;

        console.log("✅ RequisitionStatsChart: Datos configurados:", {
            total,
            toApprove: countToApprove,        // Nueva métrica
            porAbrir: countPorAbrir,          // Renombrada
            open: countApprovedOpen,
            closed: countApprovedClosed
        });
    }

    async openRequisitionList(stateCode) {
        let domain = [];

        if (stateCode === 'to_approve') {
            // ✅ Nueva condición para "Por Aprobar"
            domain.push(['state', '=', 'to_approve']);
        } else if (stateCode === 'approved_open') {
            domain.push(['state', '=', 'approved'], ['is_published', '=', true]);
        } else if (stateCode === 'approved_closed') {
            domain.push(['state', '=', 'approved'], ['is_published', '=', false], ['close_date', '!=', false]);
        } else if (stateCode === 'por_abrir') {
            // ✅ Incluir first_approval + approved no publicadas (sin close_date)
            domain.push('|', 
                ['state', '=', 'first_approval'],
                '&', ['state', '=', 'approved'], 
                '&', ['is_published', '=', false], 
                ['close_date', '=', false]
            );
        } else if (stateCode) {
            domain.push(['state', '=', stateCode]);
        }
        // Para stateCode === null (Total), no agregar ningún filtro

        console.log("🔍 Dominio aplicado:", domain);

        await this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Requisiciones${
                stateCode === 'to_approve' ? ' - Por Aprobar' : 
                stateCode === 'por_abrir' ? ' - Por Abrir' : 
                (stateCode ? ` - ${stateCode}` : ' (Todas)')
            }`,
            res_model: 'hr.requisition',
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            domain: domain,
        });
    }

    showEmptyChart() {
        this.state.hasData = false;
        this.state.chartKey = 'empty-requisition-' + Date.now();
        
        this.state.apexConfig = {
            series: [{
                name: "Sin datos",
                data: [1]
            }],
            options: {
                chart: {
                    type: 'bar',
                    height: this.props.height || 400,
                    id: 'empty-requisition-chart-' + Date.now()
                },
                xaxis: {
                    categories: ['Sin datos']
                },
                colors: ['#E0E0E0'],
                dataLabels: { enabled: false },
                legend: { show: false },
                tooltip: { enabled: false },
                title: {
                    text: 'No hay requisiciones disponibles',
                    align: 'center',
                    style: { color: '#999' }
                },
                grid: { show: false }
            }
        };
    }

    getPastelColors(count) {
        const premiumColors = [
            '#4ECDC4', // Total - Turquesa
            '#FFA07A', // Por Aprobar - Salmón (nuevo color)
            '#FFB347', // Por Abrir - Naranja suave  
            '#98D8C8', // Abiertas - Verde menta
            '#BB8FCE', // Cerradas - Lavanda
        ];

        return premiumColors.slice(0, count);
    }

    async refresh() {
        console.log("🔄 RequisitionStatsChart: Iniciando refresh...");
        this.showEmptyChart();
        await new Promise(resolve => setTimeout(resolve, 100));
        await this.loadChartData();
        console.log("✅ RequisitionStatsChart: Refresh completado");
    }
}