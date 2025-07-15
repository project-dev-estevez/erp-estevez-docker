/** @odoo-module **/

import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "hr_recruitment_estevez.KpiCard";  // ✅ CONSISTENTE con el naming

    // ✅ Props estáticas para validación
    static props = {
        name: String,                           // ✅ Nombre obligatorio: "Postulaciones"
        value: [String, Number],               // ✅ Valor: puede ser string o number
        percentage: { 
            type: [String, Number], 
            optional: true 
        },                                     // ✅ Porcentaje opcional
        showPercentage: { 
            type: Boolean, 
            optional: true 
        },                                     // ✅ Mostrar porcentaje opcional
        onClick: { 
            type: Function, 
            optional: true 
        },                                     // ✅ Función click opcional
    };

    // ✅ Defaults más completos
    static defaultProps = {
        showPercentage: false,                 
        percentage: null,                      
    };

    // ✅ Formatear el valor para mostrar
    get formattedValue() {
        if (typeof this.props.value === 'number') {
            // Si es número, agregar comas: 1000 → 1,000
            return this.props.value.toLocaleString();
        }
        return this.props.value || '0';
    }

    // ✅ Formatear el porcentaje
    get formattedPercentage() {
        if (!this.props.percentage) return null;
        
        const percentage = parseFloat(this.props.percentage);
        if (isNaN(percentage)) return null;
        
        const sign = percentage >= 0 ? '+' : '';
        return `${sign}${percentage.toFixed(1)}%`;
    }

    // ✅ Color del porcentaje según si es positivo o negativo
    get percentageColor() {
        if (!this.props.percentage) return 'text-muted';
        
        const percentage = parseFloat(this.props.percentage);
        if (isNaN(percentage)) return 'text-muted';
        
        return percentage >= 0 ? 'text-success' : 'text-danger';
    }

    // ✅ Método limpio para manejar clicks
    onCardClick() {
        if (this.props.onClick) {
            this.props.onClick();
        }
    }
}