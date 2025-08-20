/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DashboardHeader } from "../dashboard_header/dashboard_header.js";

export class EmployeesDashboard extends Component {
	static template = "hr_estevez.EmployeesDashboard";
	static components = { DashboardHeader };

	setup() {
		this.orm = useService("orm");
		this.action = useService("action");
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().slice(0, 10);
        this.state = useState({
			// Estadísticas generales
			totalEmployees: 0,
			activeEmployees: 0,
			inactiveEmployees: 0,
			newEmployeesThisMonth: 0,
			// Distribución por departamentos
			departmentData: [],
			// Distribución por áreas
			areaData: [],
			// Empleados próximos a cumpleaños
			upcomingBirthdays: [],
			// Empleados con contratos próximos a vencer
			contractsExpiring: [],
			// Estadísticas de contratos
			contractStats: {
				fixed: 0,
				indefinite: 0,
				temporary: 0
			},
			loading: true,
			startDate: firstDay,
			endDate: lastDay
		});

		onWillStart(async () => {
			await this.loadDashboardData();
		});
	}

	onDateChange = (startDate, endDate) => {
		this.state.startDate = startDate;
		this.state.endDate = endDate;
		this.loadDashboardData();
	}

	async loadDashboardData() {
		try {
			// Cargar todas las estadísticas en paralelo
			const [
				employeeStats,
				departmentStats,
				areaStats,
				birthdays,
				contracts,
				contractTypeStats
			] = await Promise.all([
				this.getEmployeeStats(),
				this.getDepartmentStats(),
				this.getAreaStats(),
				// ...existing code...

			// ...existing code...
			]);
			// ...existing code...
		} catch (error) {
			// ...existing code...
		}
	}
	// ...existing code...
}

// Registrar el componente OWL en el registry de acciones de Odoo
registry.category("actions").add("hr_estevez.EmployeesDashboard", EmployeesDashboard);
