from odoo import models

class ReportHelper(models.AbstractModel):
    _name = 'hr_attendance_estevez.report_helper'
    _description = 'Helpers para reportes de asistencias y nómina'

    def get_report_rows(self, env, report_type='attendance'):
        """
        Retorna las filas para el tipo de reporte solicitado.
        """
        if report_type == 'attendance':
            return self._get_attendance_report_rows(env)
        elif report_type == 'payroll':
            return self._get_payroll_report_rows(env)
        else:
            return []

    def _get_attendance_report_rows(self, env):
        """
        Retorna las filas para el reporte de asistencias.
        """
        return [
            ['Empleado', 'Check-In', 'Check-Out', 'Duración', 'TipoPago'],
            ['Juan Pérez', '2025-10-20 08:00', '2025-10-20 17:00', 9, 'Mensual'],
        ]

    def _get_payroll_report_rows(self, env):
        """
        Retorna las filas para el reporte de nómina.
        """
        return [
            [
                'Numero Empleado',
                'Nombre Completo',
                'Fecha de Ingreso',
                'Empresa',
                'Departamento',
                'Puesto',
                'Tipo Pago',
            ],
            [
                '0001',
                'María Gómez',
                '2022-01-15',
                'Mi Empresa S.A.',
                'Ventas',
                'Ejecutivo de Ventas',
                'Mensual',
            ],
        ]