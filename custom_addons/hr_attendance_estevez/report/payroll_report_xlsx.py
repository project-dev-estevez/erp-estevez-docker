# reports/payroll_report_xlsx.py
from odoo import models
import datetime

class PayrollReportXlsx(models.AbstractModel):
    _name = 'report.hr_attendance_estevez.report_payroll_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte Excel de Nómina (Hola Mundo)'

    def generate_xlsx_report(self, workbook, data, objects):
        # data contiene los filtros que pasó el wizard
        helper = self.env['hr_attendance_estevez.report_helper']
        rows = helper.hello_world_rows(self.env, tipo='payroll')

        sheet = workbook.add_worksheet('Nómina - Hola')
        bold = workbook.add_format({'bold': True})
        # Escribir filas simples
        for r_idx, row in enumerate(rows):
            for c_idx, cell in enumerate(row):
                fmt = bold if r_idx == 0 else None
                sheet.write(r_idx, c_idx, cell, fmt)
