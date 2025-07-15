/** @odoo-module **/

import { Component } from "@odoo/owl";

export class DashboardHeader extends Component {
    static template = "hr_recruitment_estevez.DashboardHeader";
    static props = {
        title: { type: String, optional: true },
        startDate: String,
        endDate: String,
        onDateChange: Function,
    };

    static defaultProps = {
        title: "Dashboard de Reclutamiento"
    };

    // ✅ Handlers para cambios de fecha
    onStartDateChange(ev) {
        const newStartDate = ev.target.value;
        this.props.onDateChange(newStartDate, this.props.endDate);
    }

    onEndDateChange(ev) {
        const newEndDate = ev.target.value;
        this.props.onDateChange(this.props.startDate, newEndDate);
    }

    // ✅ Nuevo: Hacer todo el contenedor clickeable
    onDateContainerClick(ev) {
        const input = ev.currentTarget.querySelector('input[type="date"]');
        if (input) {
            input.focus();
            // Mostrar el picker si está disponible
            if (input.showPicker) {
                input.showPicker();
            }
        }
    }
}