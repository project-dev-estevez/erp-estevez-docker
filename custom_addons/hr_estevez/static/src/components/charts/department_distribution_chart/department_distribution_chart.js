/** @odoo-module */

import { Component, useState, onWillStart, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class DepartmentDistributionChart extends Component {
    static template = "hr_estevez.DepartmentDistributionChart";
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
            // ✅ Configuración para ApexCharts
            apexConfig: {
                series: [],
                categories: [],
                options: {}
            },
            isLoading: true,
            hasData: false,
            // ✅ Datos internos para manejo
            departmentsData: [],
            chartKey: 'department-chart-' + Date.now()
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
            
            // ✅ Obtener datos de empleados por departamento
            const departmentData = await this.getDepartmentDistribution();

            // ✅ Configurar datos para ApexCharts
            this.setupApexChart(departmentData);            
            this.state.hasData = departmentData.length > 0;
            this.state.isLoading = false;
            
        } catch (error) {
            console.error("Error cargando gráfico de departamentos:", error);
            this.state.isLoading = false;
            this.state.hasData = false;
        }
    }

    async getDepartmentDistribution() {
        try {
            // ✅ Para distribución por departamento, mostramos TODOS los empleados activos
            // Las fechas NO aplican aquí porque queremos la distribución actual
            let domain = [['active', '=', true]]; // Solo empleados activos

            // ✅ Obtener empleados agrupados por departamento
            const employees = await this.orm.searchRead(
                'hr.employee',
                domain,
                ['department_id', 'name'] // Agregamos name para debug
            );

            // ✅ Procesar datos por departamento
            const departmentCount = {};
            let employeesWithoutDept = 0;

            employees.forEach(employee => {
                if (employee.department_id && employee.department_id[0]) {
                    const deptName = employee.department_id[1];
                    departmentCount[deptName] = (departmentCount[deptName] || 0) + 1;
                } else {
                    employeesWithoutDept++;
                }
            });

            // ✅ Agregar empleados sin departamento si los hay
            if (employeesWithoutDept > 0) {
                departmentCount['Sin Departamento'] = employeesWithoutDept;
            }

            // ✅ Convertir a array para el gráfico
            const result = Object.entries(departmentCount).map(([name, count]) => ({
                name,
                count,
                percentage: employees.length > 0 ? ((count / employees.length) * 100).toFixed(1) : 0
            }));

            // ✅ Ordenar por cantidad descendente
            const sortedResult = result.sort((a, b) => b.count - a.count);

            return sortedResult;

        } catch (error) {
            console.error("❌ Error obteniendo distribución por departamento:", error);
            return [];
        }
    }

    setupApexChart(departmentData) {
        this.state.departmentsData = departmentData;

        if (!departmentData || departmentData.length === 0) {
            this.state.apexConfig = {
                series: [],
                categories: [],
                options: {}
            };
            return;
        }

        // ✅ Preparar datos para gráfico de barras
        const series = [{
            name: 'Empleados',
            data: departmentData.map(dept => dept.count)
        }];
        const categories = departmentData.map(dept => dept.name);
        
        // ✅ Configuración del gráfico tipo barras horizontales
        const options = {
            chart: {
                type: 'bar',
                height: this.props.height || 350,
                fontFamily: 'inherit',
                toolbar: {
                    show: true
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.onDepartmentClick(config.dataPointIndex);
                    }
                }
            },
            series: series,
            colors: ['#008FFB'],
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
                    text: 'Departamentos'
                }
            },
            grid: {
                borderColor: '#f1f1f1',
                strokeDashArray: 3
            },
            tooltip: {
                custom: ({ series, seriesIndex, dataPointIndex, w }) => {
                    const dept = departmentData[dataPointIndex];
                    return `<div style="
                        background: rgba(0, 0, 0, 0.8); 
                        color: white; 
                        padding: 10px 15px; 
                        border-radius: 6px; 
                        font-size: 13px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    ">
                        <strong>${dept.name}</strong><br/>
                        Empleados: <strong>${dept.count}</strong><br/>
                        Porcentaje: <strong>${dept.percentage}%</strong>
                    </div>`;
                }
            }
        };

        this.state.apexConfig = {
            series: series,
            categories: categories,
            filename: 'distribucion_departamentos',
            options: options
        };

        // ✅ Regenerar key para forzar re-render
        this.state.chartKey = 'department-chart-' + Date.now();
    }

    onDepartmentClick(dataPointIndex) {
        const selectedDept = this.state.departmentsData[dataPointIndex];
        if (!selectedDept) return;

        console.log(`🏢 Click en departamento: ${selectedDept.name} (${selectedDept.count} empleados)`);

        // ✅ Navegar a vista de empleados filtrada por departamento
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Empleados - ${selectedDept.name}`,
            res_model: 'hr.employee',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            domain: selectedDept.name === 'Sin Departamento' 
                ? [['active', '=', true], ['department_id', '=', false]]
                : [['active', '=', true], ['department_id.name', '=', selectedDept.name]],
            context: {
                'search_default_group_by_department': 1
            }
        });
    }

    // ✅ Método para refrescar el gráfico externamente
    async refresh() {
        await this.loadChart();
    }
}
