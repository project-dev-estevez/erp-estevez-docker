/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class EmployeesDashboard extends Component {
	static template = "hr_estevez.EmployeesDashboard";

	setup() {
		this.orm = useService("orm");
		this.action = useService("action");
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
			loading: true
		});

		onWillStart(async () => {
			await this.loadDashboardData();
		});
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
			]);
			// ...existing code...
		} catch (error) {
			// ...existing code...
		}
	}
	// ...existing code...
}
