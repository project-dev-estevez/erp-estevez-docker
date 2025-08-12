/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class HREmployeesDashboard extends Component {
    static template = "hr_estevez.HREmployeesDashboard";

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
                this.getUpcomingBirthdays(),
                this.getExpiringContracts(),
                this.getContractTypeStats()
            ]);

            Object.assign(this.state, {
                ...employeeStats,
                departmentData: departmentStats,
                areaData: areaStats,
                upcomingBirthdays: birthdays,
                contractsExpiring: contracts,
                contractStats: contractTypeStats,
                loading: false
            });
        } catch (error) {
            console.error("Error cargando datos del dashboard:", error);
            this.state.loading = false;
        }
    }

    async getEmployeeStats() {
        const totalEmployees = await this.orm.searchCount("hr.employee", []);
        const activeEmployees = await this.orm.searchCount("hr.employee", [["active", "=", true]]);
        
        // Empleados nuevos este mes
        const currentDate = new Date();
        const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const newEmployeesThisMonth = await this.orm.searchCount("hr.employee", [
            ["create_date", ">=", firstDayOfMonth.toISOString().split('T')[0]]
        ]);

        return {
            totalEmployees,
            activeEmployees,
            inactiveEmployees: totalEmployees - activeEmployees,
            newEmployeesThisMonth
        };
    }

    async getDepartmentStats() {
        const departments = await this.orm.searchRead("hr.department", [], ["name"]);
        const departmentData = [];

        for (const dept of departments) {
            const count = await this.orm.searchCount("hr.employee", [
                ["department_id", "=", dept.id],
                ["active", "=", true]
            ]);
            departmentData.push({
                name: dept.name,
                count: count
            });
        }

        return departmentData.sort((a, b) => b.count - a.count);
    }

    async getAreaStats() {
        // Asumiendo que tienes un modelo hr.area
        const areas = await this.orm.searchRead("hr.area", [], ["name"]);
        const areaData = [];

        for (const area of areas) {
            const count = await this.orm.searchCount("hr.employee", [
                ["area_id", "=", area.id],
                ["active", "=", true]
            ]);
            areaData.push({
                name: area.name,
                count: count
            });
        }

        return areaData.sort((a, b) => b.count - a.count);
    }

    async getUpcomingBirthdays() {
        const currentDate = new Date();
        const nextMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, currentDate.getDate());
        
        const employees = await this.orm.searchRead("hr.employee", [
            ["birthday", "!=", false],
            ["active", "=", true]
        ], ["name", "birthday"]);

        const upcoming = employees.filter(emp => {
            if (!emp.birthday) return false;
            const birthday = new Date(emp.birthday);
            const thisYearBirthday = new Date(currentDate.getFullYear(), birthday.getMonth(), birthday.getDate());
            
            return thisYearBirthday >= currentDate && thisYearBirthday <= nextMonth;
        });

        return upcoming.slice(0, 5); // Mostrar solo los próximos 5
    }

    async getExpiringContracts() {
        const currentDate = new Date();
        const nextMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, currentDate.getDate());
        
        const contracts = await this.orm.searchRead("hr.contract", [
            ["date_end", "!=", false],
            ["date_end", "<=", nextMonth.toISOString().split('T')[0]],
            ["state", "=", "open"]
        ], ["employee_id", "date_end"]);

        return contracts.slice(0, 5); // Mostrar solo los próximos 5
    }

    async getContractTypeStats() {
        const contracts = await this.orm.searchRead("hr.contract", [
            ["state", "=", "open"]
        ], ["contract_type_id"]);

        const stats = { fixed: 0, indefinite: 0, temporary: 0 };
        
        // Esto dependerá de cómo tengas configurados los tipos de contrato
        // Por ahora asumimos que tienes tipos específicos
        for (const contract of contracts) {
            if (contract.contract_type_id) {
                const contractType = await this.orm.read("hr.contract.type", [contract.contract_type_id[0]], ["name"]);
                const typeName = contractType[0].name.toLowerCase();
                
                if (typeName.includes("fijo") || typeName.includes("fixed")) {
                    stats.fixed++;
                } else if (typeName.includes("indefinido") || typeName.includes("indefinite")) {
                    stats.indefinite++;
                } else {
                    stats.temporary++;
                }
            }
        }

        return stats;
    }

    // Métodos para navegar a diferentes vistas
    openEmployeesList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Empleados",
            res_model: "hr.employee",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openDepartmentsList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Departamentos",
            res_model: "hr.department",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openContractsList() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Contratos",
            res_model: "hr.contract",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async refreshDashboard() {
        this.state.loading = true;
        await this.loadDashboardData();
    }
}

// Registrar el componente
registry.category("actions").add("hr_employees.dashboard", HREmployeesDashboard);
