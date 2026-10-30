/** @odoo-module **/
import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "hr_estevez.KpiCard";
    static props = {
        name: { type: String },
        value: { type: Number },
        icon: { type: String, optional: true },
        color: { type: String, optional: true },
        subtitle: { type: String, optional: true },
        tooltip: { type: String, optional: true },
        onClick: { type: Function, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get hasClick() {
        return typeof this.props.onClick === 'function';
    }

    get formattedValue() {
        return (this.props.value || 0).toLocaleString("es-MX");
    }

    onCardClick() {
        if (this.hasClick) {
            this.props.onClick();
        }
    }

    onCardKeydown(ev) {
        if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            this.onCardClick();
        }
    }
}
