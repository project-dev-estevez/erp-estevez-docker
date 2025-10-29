from odoo import models


class PayrollReportXlsx(models.AbstractModel):
    _name = 'report.hr_attendance_estevez.report_payroll_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte Excel de Nómina con colores por símbolo'

    # === MÉTODO PRINCIPAL ===
    def generate_xlsx_report(self, workbook, data, objects):
        sheet = workbook.add_worksheet('Nómina')

        # Preparar datos y formatos
        rows = self._get_report_data(data)
        formats = self._define_formats(workbook)

        # Escribir encabezados y filas
        self._write_headers(sheet, rows[0], formats)
        self._write_data_rows(sheet, rows[1:], formats)

    # === MÉTODOS PRIVADOS ===

    def _get_report_data(self, data):
        """Obtiene las filas del reporte usando el helper."""
        helper = self.env['hr_attendance_estevez.report_helper']
        return helper.get_report_rows(self.env, report_type='payroll', filters=data)

    def _define_formats(self, workbook):
        """Define todos los formatos necesarios para el reporte."""
        # Formatos generales
        base = {
            'header': workbook.add_format({
                'bold': True, 'align': 'center', 'bg_color': '#D9D9D9', 'border': 1
            }),
            'center': workbook.add_format({'align': 'center', 'border': 1}),
            'bold_center': workbook.add_format({'bold': True, 'align': 'center', 'border': 1}),
        }

        # Formatos por símbolo (colores)
        symbol_colors = {
            'A': '#92D050',  # Asistencia
            'V': '#9BC2E6',  # Vacaciones
            'R': '#FFD966',  # Retardo
            'I': '#A6A6A6',  # Incapacidad
            'P': '#F4B183',  # Permiso
            'F': '#FF6666',  # Falta
        }

        base['symbols'] = {
            symbol: workbook.add_format({
                'align': 'center', 'border': 1, 'bg_color': color, 'bold': True
            })
            for symbol, color in symbol_colors.items()
        }

        return base

    def _write_headers(self, sheet, headers, formats):
        """Escribe la fila de encabezados."""
        for col, header in enumerate(headers):
            sheet.write(0, col, header, formats['header'])
            sheet.set_column(col, col, 12)

    def _write_data_rows(self, sheet, rows, formats):
        """Escribe las filas de datos."""
        for row_idx, row in enumerate(rows, start=1):
            for col_idx, cell in enumerate(row):
                fmt = self._select_format(cell, col_idx, formats)
                sheet.write(row_idx, col_idx, cell, fmt)

    def _select_format(self, cell, col_idx, formats):
        """Determina el formato correcto para cada celda."""
        # Si es un símbolo con color
        if isinstance(cell, str) and cell in formats['symbols']:
            return formats['symbols'][cell]

        # Si es texto fijo (por ejemplo, columnas de identificación)
        if col_idx < 7:
            return formats['bold_center'] if col_idx == 1 else formats['center']

        # Por defecto
        return formats['center']
