from odoo import models

class ReportHelper(models.AbstractModel):
    _name = 'hr_attendance_estevez.report_helper'
    _description = 'Helpers para reportes de asistencias y nómina'

    def hello_world_rows(self, env, tipo='attendance'):
        """
        Retorna una lista de filas de ejemplo.
        En la versión real: aquí harás búsquedas, agregaciones y transformaciones.
        """
        if tipo == 'attendance':
            return [
                ['Empleado', 'Check-In', 'Check-Out', 'Duración', 'TipoPago'],
                ['Juan Pérez', '2025-10-20 08:00', '2025-10-20 17:00', 9, 'Mensual'],
            ]
        else:
            # payroll
            return [
                ['Empleado', 'Departamento', 'Salario Base', 'Total Pagado'],
                ['María Gómez', 'Ventas', 1200.00, 1200.00],
            ]