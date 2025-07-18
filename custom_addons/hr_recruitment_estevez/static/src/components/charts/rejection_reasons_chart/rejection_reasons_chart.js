/** @odoo-module */

import { Component, useState, onWillStart, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ChartRendererApex } from "../../chart_renderer_apex/chart_renderer_apex";

export class RejectionReasonsChart extends Component {
    static template = "hr_recruitment_estevez.RejectionReasonsChart";
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
            apexConfigCandidate: {
                series: [],
                categories: [],
                options: {}
            },
            apexConfigCompany: {
                series: [],
                categories: [],
                options: {}
            },
            isLoading: true,
            hasData: false,
            candidateData: [],
            companyData: [],
            chartKeyCand: 'candidate-chart-' + Date.now(),
            chartKeyComp: 'company-chart-' + Date.now()
        });

        onWillStart(async () => {
            await this.loadChart();
        });

        onMounted(() => {
            if (this.props.onMounted) {
                this.props.onMounted(this);
            }
        });

        onWillUpdateProps(async (nextProps) => {
            if (this.props.startDate !== nextProps.startDate || 
                this.props.endDate !== nextProps.endDate) {
                
                console.log("📅 RejectionReasonsChart: Fechas cambiaron, recargando...");
                
                this.tempProps = nextProps;
                await this.loadChart();
                this.tempProps = null;
            }
        });
    }

    getCurrentProps() {
        return this.tempProps || this.props;
    }

    async loadChart() {
        const currentProps = this.getCurrentProps();
        
        console.log("📊 RejectionReasonsChart: Cargando datos...", {
            startDate: currentProps.startDate,
            endDate: currentProps.endDate
        });

        this.state.isLoading = true;

        try {
            await this.getRejectionReasons();
            console.log("✅ RejectionReasonsChart: Datos cargados correctamente");
        } catch (error) {
            console.error("❌ RejectionReasonsChart: Error cargando datos:", error);
            this.showEmptyChart();
        } finally {
            this.state.isLoading = false;
        }
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

        // ✅ FUNCIÓN AVANZADA: Normalizar texto
        const normalizeText = (text) => {
            if (!text) return '';
            
            return text
                .toLowerCase()
                .trim()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .replace(/[^\w\s]/g, ' ')
                .replace(/\s+/g, ' ')
                .trim();
        };

        // ✅ FUNCIÓN MEJORADA: Detectar si es declinación del candidato
        const isCandidateDecline = (reasonLabel) => {
            if (!reasonLabel) return false;
            
            const normalizedLabel = normalizeText(reasonLabel);
            
            const candidateDeclinePatterns = [
                'declino', 'candidato declino', 'declina', 'candidato declina',
                'no se presento', 'no se presenta', 'no asistio', 'no asiste',
                'ausente', 'falta', 'inasistencia',
                'solo se presenta a induccion', 'solo induccion',
                'no respondio', 'no responde', 'no contesta', 'no contesto',
                'sin respuesta', 'no hay respuesta',
                'abandono', 'abandona', 'se retira', 'se retiro', 'retiro',
                'desiste', 'desistio',
                'cambio de opinion', 'cambio opinion', 'ya no le interesa',
                'perdio interes', 'perdio el interes', 'sin interes',
                'acepto otra oferta', 'acepta otra oferta', 'otra oferta',
                'mejor oferta', 'oferta mejor', 'consiguio otro trabajo',
                'otro trabajo', 'otra empresa',
                'no esta interesado', 'no le interesa', 'no disponible',
                'no puede', 'imposibilitado', 'problemas personales',
                'situacion personal', 'no cumple horario', 'horario no le conviene',
                'salario insuficiente', 'salario bajo', 'sueldo bajo',
                'poco salario', 'distancia', 'muy lejos', 'ubicacion',
                'transporte', 'no acepta condiciones', 'condiciones no favorables',
                'expectativas diferentes', 'no es lo que busca', 'cambio de planes'
            ];
            
            return candidateDeclinePatterns.some(pattern => {
                return normalizedLabel === pattern || normalizedLabel.includes(pattern);
            });
        };

        // Separa en declinaciones de candidatos y rechazos de empresa
        const candidateDeclines = [];
        const companyRejections = [];

        for (const r of data) {
            const id = r.refuse_reason_id && r.refuse_reason_id[0] || false;
            const label = (r.refuse_reason_id && r.refuse_reason_id[1]) || "Sin motivo";
            const count = r.refuse_reason_id_count;

            if (isCandidateDecline(label)) {
                candidateDeclines.push({ id, label, count });
                console.log(`👤 CANDIDATO: "${label}"`);
            } else {
                companyRejections.push({ id, label, count });
                console.log(`🏢 EMPRESA: "${label}"`);
            }
        }

        console.log("📊 Resumen de clasificación de rechazos:");
        console.log(`👤 Declinaciones de candidatos: ${candidateDeclines.length} tipos, ${candidateDeclines.reduce((sum, x) => sum + x.count, 0)} total`);
        console.log(`🏢 Rechazos de empresa: ${companyRejections.length} tipos, ${companyRejections.reduce((sum, x) => sum + x.count, 0)} total`);

        // Verificar si hay datos
        if (candidateDeclines.length === 0 && companyRejections.length === 0) {
            console.log("⚠️ RejectionReasonsChart: No hay datos de rechazo");
            this.showEmptyChart();
            return;
        }

        this.state.hasData = true;
        this.state.candidateData = candidateDeclines;
        this.state.companyData = companyRejections;

        // ✅ CONFIGURAR GRÁFICA DE CANDIDATOS (COMO TU EJEMPLO)
        if (candidateDeclines.length > 0) {
            const labelsCandidate = candidateDeclines.map(x => x.label);
            const seriesCandidate = candidateDeclines.map(x => x.count);
            const colorsCandidate = this.getBarColors(labelsCandidate.length, 'candidate');

            this.state.chartKeyCand = 'candidate-chart-' + Date.now();

            this.state.apexConfigCandidate = {
                series: [{
                    name: 'Declinaciones',
                    data: seriesCandidate // ✅ Solo los números como en tu ejemplo
                }],
                options: {
                    title: {
                        text: 'Declinaciones de Candidatos',
                        align: 'center',
                        style: {
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#dc3545'
                        }
                    },
                    chart: {
                        type: 'bar',
                        height: this.props.height || 350,
                        id: 'candidate-rejections-' + Date.now(),
                        events: {
                            dataPointSelection: (event, chartContext, config) => {
                                const reasonData = this.state.candidateData[config.dataPointIndex];
                                this.openRejectionList(reasonData.id);
                            }
                        }
                    },
                    plotOptions: {
                        bar: {
                            borderRadius: 4,
                            borderRadiusApplication: 'end',
                            horizontal: true, // ✅ Como en tu ejemplo
                        }
                    },
                    colors: colorsCandidate,
                    dataLabels: {
                        enabled: true, // ✅ CAMBIÉ: Habilitado para mostrar números
                        formatter: function (val) {
                            return val;
                        },
                        style: {
                            colors: ['#fff'],
                            fontSize: '12px',
                            fontWeight: 'bold'
                        }
                    },
                    xaxis: {
                        categories: labelsCandidate, // ✅ EXACTO como en tu ejemplo
                        labels: {
                            style: {
                                fontSize: '10px'
                            }
                        }
                    },
                    // ✅ QUITAR toda la configuración de yaxis.categories
                    yaxis: {
                        labels: {
                            style: {
                                fontSize: '10px'
                            }
                        }
                    },
                    tooltip: {
                        y: {
                            formatter: function (value, { dataPointIndex }) {
                                const total = candidateDeclines.reduce((sum, x) => sum + x.count, 0);
                                const percent = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                                return `${value} declinaciones (${percent}%)`;
                            }
                        }
                    },
                    responsive: [{
                        breakpoint: 480,
                        options: {
                            chart: {
                                height: 400
                            },
                            xaxis: {
                                labels: {
                                    style: {
                                        fontSize: '9px'
                                    }
                                }
                            }
                        }
                    }]
                }
            };
        }

        // ✅ CONFIGURAR GRÁFICA DE EMPRESA (COMO TU EJEMPLO)
        if (companyRejections.length > 0) {
            const labelsCompany = companyRejections.map(x => x.label);
            const seriesCompany = companyRejections.map(x => x.count);
            const colorsCompany = this.getBarColors(labelsCompany.length, 'company');

            this.state.chartKeyComp = 'company-chart-' + Date.now();

            this.state.apexConfigCompany = {
                series: [{
                    name: 'Rechazos',
                    data: seriesCompany // ✅ Solo los números como en tu ejemplo
                }],
                options: {
                    title: {
                        text: 'Rechazos de la Empresa',
                        align: 'center',
                        style: {
                            fontSize: '16px',
                            fontWeight: 'bold',
                            color: '#28a745'
                        }
                    },
                    chart: {
                        type: 'bar',
                        height: this.props.height || 350,
                        id: 'company-rejections-' + Date.now(),
                        events: {
                            dataPointSelection: (event, chartContext, config) => {
                                const reasonData = this.state.companyData[config.dataPointIndex];
                                this.openRejectionList(reasonData.id);
                            }
                        }
                    },
                    plotOptions: {
                        bar: {
                            borderRadius: 4,
                            borderRadiusApplication: 'end',
                            horizontal: true, // ✅ Como en tu ejemplo
                        }
                    },
                    colors: colorsCompany,
                    dataLabels: {
                        enabled: true, // ✅ CAMBIÉ: Habilitado para mostrar números
                        formatter: function (val) {
                            return val;
                        },
                        style: {
                            colors: ['#fff'],
                            fontSize: '12px',
                            fontWeight: 'bold'
                        }
                    },
                    xaxis: {
                        categories: labelsCompany, // ✅ EXACTO como en tu ejemplo
                        labels: {
                            style: {
                                fontSize: '10px'
                            }
                        }
                    },
                    // ✅ QUITAR toda la configuración de yaxis.categories
                    yaxis: {
                        labels: {
                            style: {
                                fontSize: '10px'
                            }
                        }
                    },
                    tooltip: {
                        y: {
                            formatter: function (value, { dataPointIndex }) {
                                const total = companyRejections.reduce((sum, x) => sum + x.count, 0);
                                const percent = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
                                return `${value} rechazos (${percent}%)`;
                            }
                        }
                    },
                    responsive: [{
                        breakpoint: 480,
                        options: {
                            chart: {
                                height: 400
                            },
                            xaxis: {
                                labels: {
                                    style: {
                                        fontSize: '9px'
                                    }
                                }
                            }
                        }
                    }]
                }
            };
        }

        console.log("✅ RejectionReasonsChart: Configuraciones ApexCharts preparadas");
    }

    async openRejectionList(refuse_reason_id) {
        const currentProps = this.getCurrentProps();
        let domain = [["application_status", "=", "refused"]];

        if (refuse_reason_id === false) {
            domain.push(["refuse_reason_id", "=", false]);
        } else if (refuse_reason_id) {
            domain.push(["refuse_reason_id", "=", refuse_reason_id]);
        } else {
            domain.push("|", 
                   ["refuse_reason_id", "=", false],
                   ["refuse_reason_id", "=", null]);
        }

        domain = this._addDateRangeToDomain(domain);

        await this.actionService.doAction({
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

    showEmptyChart() {
        this.state.hasData = false;
        this.state.chartKeyCand = 'empty-candidate-' + Date.now();
        this.state.chartKeyComp = 'empty-company-' + Date.now();
        
        this.state.apexConfigCandidate = {
            series: [],
            categories: [],
            options: { chart: { id: 'empty-candidate-chart-' + Date.now() } }
        };
        
        this.state.apexConfigCompany = {
            series: [],
            categories: [],
            options: { chart: { id: 'empty-company-chart-' + Date.now() } }
        };
        
        this.state.candidateData = [];
        this.state.companyData = [];
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

    getBarColors(count, type) {
        // Colores para candidatos (rojos/naranjas)
        const candidateColors = [
            '#FF6B6B', '#FF8E8E', '#FFA8A8', '#FFB3B3', '#FFC2C2',
            '#FFD1D1', '#FF9999', '#FF7777', '#FF5555', '#FF4444'
        ];
        
        // Colores para empresa (verdes/azules)
        const companyColors = [
            '#4ECDC4', '#45B7D1', '#96CEB4', '#85C1E9', '#A3E4D7',
            '#AED6F1', '#A9DFBF', '#D5DBDB', '#7FB3D3', '#5DADE2'
        ];
        
        const baseColors = type === 'candidate' ? candidateColors : companyColors;
        
        if (count <= baseColors.length) {
            return baseColors.slice(0, count);
        }

        const colors = [...baseColors];
        const baseHue = type === 'candidate' ? 0 : 180; // Rojo para candidatos, azul para empresa
        
        for (let i = baseColors.length; i < count; i++) {
            const hue = baseHue + (i - baseColors.length) * 20;
            const saturation = 70 + Math.random() * 15;
            const lightness = 50 + Math.random() * 20;
            colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }
        
        return colors;
    }

    async refresh() {
        console.log("🔄 RejectionReasonsChart: Iniciando refresh...");
        this.showEmptyChart();
        await new Promise(resolve => setTimeout(resolve, 100));
        await this.loadChart();
        console.log("✅ RejectionReasonsChart: Refresh completado");
    }
}