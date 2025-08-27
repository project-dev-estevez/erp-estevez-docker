/** @odoo-module **/

import { Component } from "@odoo/owl";

export class DashboardHeader extends Component {
    static template = "hr_estevez.DashboardHeader";
    static props = {
        title: { type: String, optional: true },
        startDate: String,
        endDate: String,
        onDateChange: Function,
    };

    static defaultProps = {
        title: "Dashboard de Empleados"
    };

    onStartDateChange(ev) {
        const newStartDate = ev.target.value;
        this.props.onDateChange(newStartDate, this.props.endDate);
    }

    onEndDateChange(ev) {
        const newEndDate = ev.target.value;
        this.props.onDateChange(this.props.startDate, newEndDate);
    }

    onDateContainerClick(ev) {
        const input = ev.currentTarget.querySelector('input[type="date"]');
        if (input) {
            input.focus();
            if (input.showPicker) {
                input.showPicker();
            }
        }
    }
}
