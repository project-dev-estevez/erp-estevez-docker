/** @odoo-module */

const { Component } = owl

export class KpiCard extends Component {
    static defaultProps = {
        showPercentage: true,
    }

}

KpiCard.template = "recruitment.kpi.card";