# reports/attendance_report_xlsx.py
from odoo import models

class AttendanceReportXlsx(models.AbstractModel):
    _name = 'report.hr_attendance_estevez.report_attendance_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte Excel de Asistencias (Hola Mundo)'

    def generate_xlsx_report(self, workbook, data, objects):
        helper = self.env['hr_attendance_estevez.report_helper']
        rows = helper.get_report_rows(self.env, report_type='attendance', filters=data)

        sheet = workbook.add_worksheet('Asistencias - Hola')
        bold = workbook.add_format({'bold': True})

        for col in range(len(rows[0])):
            sheet.set_column(col, col, 25)
            
        for r_idx, row in enumerate(rows):
            for c_idx, cell in enumerate(row):
                fmt = bold if r_idx == 0 else None
                sheet.write(r_idx, c_idx, cell, fmt)
