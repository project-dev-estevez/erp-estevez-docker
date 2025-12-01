/** @odoo-module */

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class GenderDistributionChart extends Component {
    static template = "hr_estevez.GenderDistributionChart";
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
                filename: 'empleados_por_genero',
                options: {}
            },
            isLoading: true,
            hasData: false,
            genderData: [],
            chartKey: 'gender-chart-' + Date.now()
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
            
            const genderData = await this.getGenderDistribution();
            this.setupApexChart(genderData);
            
            this.state.hasData = genderData.length > 0;
            this.state.isLoading = false;
            
        } catch (error) {
            console.error("Error cargando gráfico de género:", error);
            this.state.isLoading = false;
            this.state.hasData = false;
        }
    }

    async getGenderDistribution() {
        try {
            // Solo empleados activos
            const domain = [['active', '=', true]];

            const employees = await this.orm.searchRead(
                'hr.employee',
                domain,
                ['gender', 'name', 'id']
            );

            console.log(" Total empleados activos:", employees.length);

            // Mapeo de valores técnicos a etiquetas legibles
            const genderLabels = {
                'male': 'Masculino',
                'female': 'Femenino',
                'indistinct': 'Indistinto',
                'other': 'Otro'
            };

            // Colores para cada género
            const genderColors = {
                'male': '#008FFB',      // Azul
                'female': '#FF4560',    // Rosa/Rojo
                'other': '#00E396'      // Verde
            };

            // Contar por género
            const genderCount = {};
            let employeesWithoutGender = 0;

            employees.forEach(employee => {
                if (employee.gender) {
                    const genderKey = employee.gender;
                    if (!genderCount[genderKey]) {
                        genderCount[genderKey] = {
                            name: genderLabels[genderKey] || genderKey,
                            count: 0,
                            employeeIds: [],
                            color: genderColors[genderKey] || '#775DD0',
                            technicalValue: genderKey
                        };
                    }
                    genderCount[genderKey].count++;
                    genderCount[genderKey].employeeIds.push(employee.id);
                } else {
                    employeesWithoutGender++;
                }
            });

            // Convertir a array
            let result = Object.values(genderCount);

            // Agregar empleados sin género si los hay
            if (employeesWithoutGender > 0) {
                const employeesWithoutGenderIds = employees
                    .filter(emp => !emp.gender)
                    .map(emp => emp.id);
                
                result.push({
                    name: 'Sin Especificar',
                    count: employeesWithoutGender,
                    employeeIds: employeesWithoutGenderIds,
                    color: '#B0B0B0',
                    technicalValue: false,
                    isWithoutGender: true
                });
            }

            // Ordenar por cantidad descendente
            result = result.sort((a, b) => b.count - a.count);

            // Calcular porcentajes
            const total = employees.length;
            result = result.map(gender => ({
                ...gender,
                percentage: total > 0 ? ((gender.count / total) * 100).toFixed(1) : 0
            }));

            console.log(" Distribución por género:", result);
            
            return result;

        } catch (error) {
            console.error(" Error obteniendo distribución por género:", error);
            return [];
        }
    }

    setupApexChart(genderData) {
        this.state.genderData = genderData;

        if (!genderData || genderData.length === 0) {
            this.state.apexConfig = {
                series: [],
                labels: [],
                filename: 'empleados_por_genero',
                options: {}
            };
            return;
        }

        // Preparar datos para gráfico de dona
        const series = genderData.map(gender => gender.count);
        const labels = genderData.map(gender => gender.name);
        const colors = genderData.map(gender => gender.color);

        // Calcular total para porcentajes
        const total = genderData.reduce((sum, item) => sum + item.count, 0);

        // Configuración del gráfico tipo donut
        const options = {
            chart: {
                type: 'donut',
                height: this.props.height || 350,
                fontFamily: 'inherit',
                toolbar: {
                    show: true
                },
                events: {
                    dataPointSelection: (event, chartContext, config) => {
                        this.onGenderClick(config.dataPointIndex);
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
                    const count = genderData[opts.seriesIndex].count;
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
            plotOptions: {
                pie: {
                    donut: {
                        size: '65%',
                        labels: {
                            show: true,
                            name: {
                                show: true,
                                fontSize: '16px',
                                fontWeight: 600
                            },
                            value: {
                                show: true,
                                fontSize: '24px',
                                fontWeight: 'bold',
                                formatter: (val) => val
                            },
                            total: {
                                show: true,
                                label: 'Total',
                                fontSize: '14px',
                                fontWeight: 600,
                                formatter: () => total
                            }
                        }
                    }
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
            filename: 'empleados_por_genero',
            options: options
        };

        this.state.chartKey = 'gender-chart-' + Date.now();
    }

    async onGenderClick(dataPointIndex) {
        const selectedGender = this.state.genderData[dataPointIndex];
        if (!selectedGender) return;

        console.log(` Click en género: ${selectedGender.name} (${selectedGender.count} empleados)`);

        let domain;

        // Determinar dominio según el género
        if (selectedGender.isWithoutGender) {
            // Sin género especificado
            domain = [['active', '=', true], ['gender', '=', false]];
        } else {
            // Género específico
            domain = [['active', '=', true], ['gender', '=', selectedGender.technicalValue]];
        }

        // Navegar a vista de empleados filtrada por género
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Empleados - ${selectedGender.name}`,
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
