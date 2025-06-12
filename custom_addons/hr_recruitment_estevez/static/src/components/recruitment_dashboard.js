/** @odoo-module **/

import { registry } from "@web/core/registry";
import { KpiCard } from "./kpi_card/kpi_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { useService } from "@web/core/utils/hooks";
import { parseDate, formatDate } from "@web/core/l10n/dates";
import { Component, onWillStart, useState } from "@odoo/owl";
const { DateTime } = luxon;

export class RecruitmentDashboard extends Component {

    setup() {
        this.state = useState({
            filledVacancies: {
                value: 10,
                percentage: 50,
            },
            period: 30,
            currentDate: DateTime.now().minus({ days: 30 }).toISODate(),
            previusDate: DateTime.now().minus({ days: 60 }).toISODate()
        })
        this.orm = useService("orm");

        onWillStart(async () => {
            this.getDates();
            await this.getFilledVacancies();
        });
    }

    async onPeriodChange() {
        this.getDates();
        await this.getFilledVacancies();
    }

    async getFilledVacancies() {
        let domain = [];
        if (this.state.period > 0) {
            domain.push(["create_date", ">", this.state.currentDate]);
        }

        const data = await this.orm.searchCount("hr.applicant", domain);
        this.state.filledVacancies.value = data;

        // Periodo previo
        let previousDomain = [];
        if (this.state.period > 0) {
            previousDomain.push(
                ["create_date", ">", this.state.previusDate],
                ["create_date", "<=", this.state.currentDate]
            );
        }
        const previousData = await this.orm.searchCount("hr.applicant", previousDomain);
        const percentage = ((data - previousData) / previousData) * 100;
        this.state.filledVacancies.percentage = percentage.toFixed(2) || 0;

        console.log(this.state.previusDate, this.state.currentDate);
    }

    getDates() {
        this.state.currentDate = DateTime.now().minus({ days: this.state.period }).toISODate();
        this.state.previusDate = DateTime.now().minus({ days: this.state.period * 2 }).toISODate();
    }


}

RecruitmentDashboard.template = "recruitment.dashboard";
RecruitmentDashboard.components = { KpiCard, ChartRenderer };

// Registrar el dashboard OWL
registry.category("actions").add("recruitment.dashboard", RecruitmentDashboard);