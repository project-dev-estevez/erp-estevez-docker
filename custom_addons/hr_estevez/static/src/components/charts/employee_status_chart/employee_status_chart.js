/** @odoo-module */

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";
import { serializeDate } from "@web/core/l10n/dates";

export class EmployeeStatusChart extends Component {
    static template = "hr_estevez.EmployeeStatusChart";
    static components = { ChartRendererApex };
    static props = {
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
                labels: [],
                filename: 'empleados_por_estado',
                options: {}
            },
            isLoading: true,
            hasData: false,
            statusData: [],
            chartKey: 'status-chart-' + Date.now()
        });

        onWillStart(async () => {
            await this.loadChart();
        });

        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });
    }

    async loadChart() {
        try {
            this.state.isLoading = true;
            
            const statusData = await this.getEmployeesByStatus();
            this.setupApexChart(statusData);
            
            this.state.hasData = statusData.length > 0;
            this.state.isLoading = false;
            
        } catch (error) {
            console.error("Error cargando gráfico de estados:", error);
            this.state.isLoading = false;
            this.state.hasData = false;
        }
    }

    async getEmployeesByStatus() {
        try {
            // Obtener todos los empleados (activos e inactivos)
            const domain = ['|', ['active', '=', true], ['active', '=', false]];

            const allEmployees = await this.orm.searchRead(
                'hr.employee',
                domain,
                ['active', 'name', 'id']
            );

            // Obtener empleados de vacaciones (ausencias validadas activas hoy marcadas como vacaciones)
            const now = luxon.DateTime.now();
            const todayStart = now.startOf('day').toUTC().toISO();
            const todayEnd = now.endOf('day').toUTC().toISO();
            
            // Primero obtener los tipos de ausencia que son vacaciones
            const vacationTypes = await this.orm.searchRead(
                'hr.leave.type',
                [['is_vacation', '=', true]],
                ['id']
            );
            const vacationTypeIds = vacationTypes.map(t => t.id);
            
            // Si no hay tipos marcados como vacaciones, buscar por nombre
            let vacationDomain;
            if (vacationTypeIds.length > 0) {
                vacationDomain = [
                    ['state', '=', 'validate'],
                    ['date_from', '<=', todayEnd],
                    ['date_to', '>=', todayStart],
                    ['holiday_status_id', 'in', vacationTypeIds]
                ];
            } else {
                // Fallback: buscar por nombre si no hay tipos marcados
                vacationDomain = [
                    ['state', '=', 'validate'],
                    ['date_from', '<=', todayEnd],
                    ['date_to', '>=', todayStart],
                    '|', ['holiday_status_id.name', 'ilike', 'vacacion'],
                    ['holiday_status_id.name', 'ilike', 'vacation']
                ];
            }
            
            const vacationLeaves = await this.orm.searchRead(
                'hr.leave',
                vacationDomain,
                ['employee_id']
            );

            // IDs de empleados en vacaciones
            const employeesOnVacationIds = new Set(
                vacationLeaves.map(leave => leave.employee_id[0])
            );

            // Contar por estado
            let activeCount = 0;
            let inactiveCount = 0;
            let onVacationCount = 0;

            allEmployees.forEach(employee => {
                if (employee.active) {
                    if (employeesOnVacationIds.has(employee.id)) {
                        onVacationCount++;
                    } else {
                        activeCount++;
                    }
                } else {
                    inactiveCount++;
                }
            });

            // Preparar resultado
            const result = [
                { name: 'Activos', count: activeCount, color: '#00E396' },
                { name: 'De Vacaciones', count: onVacationCount, color: '#008FFB' },
                { name: 'Inactivos', count: inactiveCount, color: '#FEB019' }
            ];

            // Solo incluir categorías con datos
            const filtered = result.filter(item => item.count > 0);
            
            return filtered;

        } catch (error) {
            console.error("❌ Error obteniendo empleados por estado:", error);
            return [];
        }
    }

    setupApexChart(statusData) {
        this.state.statusData = statusData;

        if (!statusData || statusData.length === 0) {
            this.state.apexConfig = {
                series: [],
                labels: [],
                filename: 'empleados_por_estado',
                options: {}
            };
            return;
        }

        // Preparar datos para gráfico de torta
        const series = statusData.map(status => status.count);
        const labels = statusData.map(status => status.name);
        const colors = statusData.map(status => status.color);

        // Calcular total para porcentajes
        const total = statusData.reduce((sum, item) => sum + item.count, 0);

        // Configuración del gráfico tipo pie
        const options = {
            chart: {
                type: 'pie',
                height: this.props.height || 350,
                fontFamily: 'inherit',
                toolbar: {
                    show: true
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.onStatusClick(config.dataPointIndex);
                    }
                }
            },
            series: series,
            labels: labels,
            colors: colors,
            legend: {
                position: 'bottom',
                horizontalAlign: 'center',
                fontSize: '14px'
            },
            dataLabels: {
                enabled: true,
                formatter: (val, opts) => {
                    const count = statusData[opts.seriesIndex].count;
                    return `${count}`;
                },
                style: {
                    fontSize: '14px',
                    fontWeight: 'bold',
                    colors: ['#fff']
                },
                dropShadow: {
                    enabled: true,
                    top: 1,
                    left: 1,
                    blur: 1,
                    opacity: 0.45
                }
            },
            tooltip: {
                y: {
                    formatter: (val, opts) => {
                        const percentage = ((val / total) * 100).toFixed(1);
                        return `${val} empleados (${percentage}%)`;
                    }
                }
            },
            responsive: [{
                breakpoint: 480,
                options: {
                    chart: {
                        width: 300
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }]
        };

        this.state.apexConfig = {
            series: series,
            labels: labels,
            filename: 'empleados_por_estado',
            options: options
        };

        this.state.chartKey = 'status-chart-' + Date.now();
    }

    async onStatusClick(dataPointIndex) {
        const selectedStatus = this.state.statusData[dataPointIndex];
        if (!selectedStatus) return;

        console.log(`📊 Click en estado: ${selectedStatus.name} (${selectedStatus.count} empleados)`);

        let domain;

        // Determinar dominio según el estado
        if (selectedStatus.name === 'De Vacaciones') {
            // Obtener IDs de empleados en vacaciones
            const now = luxon.DateTime.now();
            const todayStart = now.startOf('day').toUTC().toISO();
            const todayEnd = now.endOf('day').toUTC().toISO();
            
            // Obtener tipos de vacaciones
            const vacationTypes = await this.orm.searchRead(
                'hr.leave.type',
                [['is_vacation', '=', true]],
                ['id']
            );
            const vacationTypeIds = vacationTypes.map(t => t.id);
            
            // Dominio para buscar ausencias
            let vacationDomain;
            if (vacationTypeIds.length > 0) {
                vacationDomain = [
                    ['state', '=', 'validate'],
                    ['date_from', '<=', todayEnd],
                    ['date_to', '>=', todayStart],
                    ['holiday_status_id', 'in', vacationTypeIds]
                ];
            } else {
                vacationDomain = [
                    ['state', '=', 'validate'],
                    ['date_from', '<=', todayEnd],
                    ['date_to', '>=', todayStart],
                    '|', ['holiday_status_id.name', 'ilike', 'vacacion'],
                    ['holiday_status_id.name', 'ilike', 'vacation']
                ];
            }
            
            const vacationLeaves = await this.orm.searchRead(
                'hr.leave',
                vacationDomain,
                ['employee_id']
            );
            const employeeIds = vacationLeaves.map(leave => leave.employee_id[0]);
            domain = [['id', 'in', employeeIds]];
        } else {
            const isActive = selectedStatus.name === 'Activos';
            domain = [['active', '=', isActive]];
        }

        // Navegar a vista de empleados filtrada por estado
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Empleados ${selectedStatus.name}`,
            res_model: 'hr.employee',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: {},
            clearBreadcrumbs: true
        });
    }

    async refresh() {
        await this.loadChart();
    }
}
