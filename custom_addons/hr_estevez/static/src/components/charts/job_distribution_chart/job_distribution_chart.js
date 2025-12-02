/** @odoo-module */

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class JobDistributionChart extends Component {
    static template = "hr_estevez.JobDistributionChart";
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
                categories: [],
                options: {}
            },
            isLoading: true,
            hasData: false,
            jobsData: [],
            chartKey: 'job-chart-' + Date.now()
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
            
            const jobData = await this.getJobDistribution();
            this.setupApexChart(jobData);
            
            this.state.hasData = jobData.length > 0;
            this.state.isLoading = false;
            
        } catch (error) {
            console.error("Error cargando gráfico de puestos:", error);
            this.state.isLoading = false;
            this.state.hasData = false;
        }
    }

    async getJobDistribution() {
        try {
            // Solo empleados activos
            const domain = [['active', '=', true]];

            const employees = await this.orm.searchRead(
                'hr.employee',
                domain,
                ['job_id', 'name', 'id']
            );

            // Procesar datos por puesto
            const jobCount = {};
            let employeesWithoutJob = 0;

            employees.forEach(employee => {
                if (employee.job_id && employee.job_id[0]) {
                    const jobName = employee.job_id[1];
                    if (!jobCount[jobName]) {
                        jobCount[jobName] = {
                            name: jobName,
                            count: 0,
                            employeeIds: []
                        };
                    }
                    jobCount[jobName].count++;
                    jobCount[jobName].employeeIds.push(employee.id);
                } else {
                    employeesWithoutJob++;
                }
            });

            // Convertir a array y ordenar por cantidad descendente
            let result = Object.values(jobCount).sort((a, b) => b.count - a.count);

            // Agregar empleados sin puesto si los hay
            if (employeesWithoutJob > 0) {
                // Obtener IDs de empleados sin job_id
                const employeesWithoutJobIds = employees
                    .filter(emp => !emp.job_id || !emp.job_id[0])
                    .map(emp => emp.id);
                
                result.push({
                    name: 'Sin Puesto Asignado',
                    count: employeesWithoutJob,
                    employeeIds: employeesWithoutJobIds,
                    isWithoutJob: true
                });
            }

            // Calcular porcentajes
            const total = employees.length;
            result = result.map(job => ({
                ...job,
                percentage: total > 0 ? ((job.count / total) * 100).toFixed(1) : 0
            }));

            return result;

        } catch (error) {
            console.error("❌ Error obteniendo distribución por puesto:", error);
            return [];
        }
    }

    setupApexChart(jobData) {
        this.state.jobsData = jobData;

        if (!jobData || jobData.length === 0) {
            this.state.apexConfig = {
                series: [],
                categories: [],
                options: {}
            };
            return;
        }

        // Preparar datos para gráfico de barras
        const series = [{
            name: 'Empleados',
            data: jobData.map(job => job.count)
        }];
        const categories = jobData.map(job => job.name);
        
        // Configuración del gráfico tipo barras horizontales
        // Altura dinámica: mínimo 350px, máximo según cantidad de puestos (40px por puesto)
        const dynamicHeight = Math.max(350, jobData.length * 40);
        
        const options = {
            chart: {
                type: 'bar',
                height: dynamicHeight,
                fontFamily: 'inherit',
                toolbar: {
                    show: true
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.onJobClick(config.dataPointIndex);
                    }
                }
            },
            series: series,
            colors: ['#00E396'],
            plotOptions: {
                bar: {
                    horizontal: true,
                    barHeight: '70%',
                    distributed: false,
                    dataLabels: {
                        position: 'center'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: (val) => `${val}`,
                style: {
                    colors: ['#fff'],
                    fontSize: '12px',
                    fontWeight: 'bold'
                }
            },
            xaxis: {
                categories: categories,
                title: {
                    text: 'Número de Empleados'
                }
            },
            yaxis: {
                title: {
                    text: 'Puestos de Trabajo'
                }
            },
            grid: {
                borderColor: '#f1f1f1',
                strokeDashArray: 3
            },
            tooltip: {
                custom: ({ series, seriesIndex, dataPointIndex, w }) => {
                    const job = jobData[dataPointIndex];
                    return `<div style="
                        background: rgba(0, 0, 0, 0.8); 
                        color: white; 
                        padding: 10px 15px; 
                        border-radius: 6px; 
                        font-size: 13px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    ">
                        <strong>${job.name}</strong><br/>
                        Empleados: <strong>${job.count}</strong><br/>
                        Porcentaje: <strong>${job.percentage}%</strong>
                    </div>`;
                }
            }
        };

        this.state.apexConfig = {
            series: series,
            categories: categories,
            filename: 'empleados_por_puesto',
            options: options
        };

        this.state.chartKey = 'job-chart-' + Date.now();
    }

    async onJobClick(dataPointIndex) {
        const selectedJob = this.state.jobsData[dataPointIndex];
        if (!selectedJob) return;

        let domain;
        let name = `Empleados - ${selectedJob.name}`;

        // Determinar dominio según el tipo de categoría
        if (selectedJob.isWithoutJob) {
            // Sin puesto asignado
            domain = [['active', '=', true], ['job_id', '=', false]];
        } else if (selectedJob.isOthers) {
            // Otros puestos (usar lista de IDs)
            domain = [['active', '=', true], ['id', 'in', selectedJob.employeeIds]];
        } else {
            // Puesto específico
            domain = [['active', '=', true], ['job_id', '=', selectedJob.name]];
        }

        // Navegar a vista de empleados filtrada por puesto
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: name,
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
