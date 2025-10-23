from odoo import models

class PayrollReportXlsx(models.AbstractModel):
    _name = 'report.hr_attendance_estevez.report_payroll_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte Excel de Nómina con colores por símbolo'

    def generate_xlsx_report(self, workbook, data, objects):
        helper = self.env['hr_attendance_estevez.report_helper']
        rows = helper.get_report_rows(self.env, report_type='payroll', filters=data)

        sheet = workbook.add_worksheet('Nómina')

        # --- FORMATOS GENERALES ---
        header_fmt = workbook.add_format({
            'bold': True, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1
        })
        center_fmt = workbook.add_format({'align': 'center', 'border': 1})
        bold_center = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})

        # --- FORMATOS POR COLOR (símbolos) ---
        colors = {
            'A': '#92D050',  # Verde claro (Asistencia)
            'V': '#9BC2E6',  # Amarillo (Vacaciones)
            'R': '#FFD966',  # Azul (Retardo)
            'I': '#A6A6A6',  # Gris (Incapacidad)
            'P': '#F4B183',  # Naranja (Permiso)
            'F': '#FF6666',  # Rojo (Falta)
        }
        symbol_formats = {
            key: workbook.add_format({
                'align': 'center',
                'border': 1,
                'bg_color': color,
                'bold': True
            })
            for key, color in colors.items()
        }

        # --- Escribir filas ---
        for r_idx, row in enumerate(rows):
            for c_idx, cell in enumerate(row):
                # Primera fila → encabezado
                if r_idx == 0:
                    sheet.write(r_idx, c_idx, cell, header_fmt)
                    sheet.set_column(c_idx, c_idx, 12)  # ancho automático aproximado
                else:
                    fmt = center_fmt
                    # Aplicar formato por símbolo si corresponde
                    if isinstance(cell, str) and cell in symbol_formats:
                        fmt = symbol_formats[cell]
                    elif r_idx > 0 and c_idx < 7:  # columnas fijas de texto
                        fmt = bold_center if c_idx == 1 else center_fmt
                    sheet.write(r_idx, c_idx, cell, fmt)
