/** @odoo-module **/
import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "hr_estevez.KpiCard";
    static props = {
        name: { type: String },
        value: { type: Number },
        secondaryValue: { type: Number, optional: true },
        showSecondaryValue: { type: Boolean, optional: true },
        onClick: { type: Function, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get hasClick() {
        return typeof this.props.onClick === 'function';
    }

    onCardClick() {
        if (this.hasClick) {
            this.props.onClick();
        }
    }
}
