from odoo import http
from odoo.http import request
import base64
from io import BytesIO

class HrEmployeeController(http.Controller):

    @http.route('/download/employee/documents/<int:employee_id>', type='http', auth='user')
    def download_employee_documents(self, employee_id, **kwargs):
        employee = request.env['hr.employee'].browse(employee_id)
        if not employee:
            return request.not_found()

        # Buscar todos los documentos relacionados con el empleado
        attachments = request.env['ir.attachment'].search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', employee.id)
        ])

        if not attachments:
            return request.not_found()

        # Crear un objeto para combinar PDFs
        from PyPDF2 import PdfMerger
        pdf_merger = PdfMerger()

        for attachment in attachments:
            if attachment.mimetype == 'application/pdf':
                pdf_content = BytesIO(base64.b64decode(attachment.datas))
                pdf_merger.append(pdf_content)

        # Guardar el PDF combinado en memoria
        combined_pdf = BytesIO()
        pdf_merger.write(combined_pdf)
        pdf_merger.close()

        # Preparar el archivo para la descarga
        combined_pdf.seek(0)
        pdf_data = combined_pdf.read()

        # Enviar el archivo como respuesta HTTP
        return request.make_response(pdf_data, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="Documentos_Empleado_{employee.id}.pdf"')
        ])