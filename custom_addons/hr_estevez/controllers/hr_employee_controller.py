from odoo import http
from odoo.http import request
import base64
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)

class HrEmployeeController(http.Controller):

    @http.route('/download/employee/documents/<int:employee_id>', type='http', auth='user')
    def download_employee_documents(self, employee_id, **kwargs):
        employee = request.env['hr.employee'].browse(employee_id)
        if not employee:
            return request.not_found()

        attachments = request.env['ir.attachment'].search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', employee.id)
        ])

        if not attachments:
            return request.redirect(f"/web#id={employee_id}&model=hr.employee&view_type=form")

        from PyPDF2 import PdfMerger, PdfReader
        pdf_merger = PdfMerger()
        encrypted_files = []

        for attachment in attachments:
            if attachment.mimetype == 'application/pdf':
                try:
                    pdf_bytes = base64.b64decode(attachment.datas)
                    if b"/Encrypt" in pdf_bytes[:2048]:
                        encrypted_files.append(attachment.name or f"ID {attachment.id}")
                        continue
                    pdf_content = BytesIO(pdf_bytes)
                    pdf_merger.append(pdf_content)
                except Exception as e:
                    _logger.error(f"Error al procesar PDF adjunto {attachment.id}: {str(e)}")

        # 🚨 Caso de error → redirigir a la vista del empleado con mensaje en querystring
        if encrypted_files:
            msg = "Los siguientes documentos están protegidos con clave: " + ", ".join(encrypted_files)
            return request.redirect(f"/web#id={employee_id}&model=hr.employee&view_type=form&error={msg}")

        if not pdf_merger.pages:
            msg = "No se encontraron documentos PDF válidos para este empleado."
            return request.redirect(f"/web#id={employee_id}&model=hr.employee&view_type=form&error={msg}")

        combined_pdf = BytesIO()
        pdf_merger.write(combined_pdf)
        pdf_merger.close()
        combined_pdf.seek(0)
        pdf_data = combined_pdf.read()

        return request.make_response(pdf_data, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename=\"Documentos_Empleado_{employee.id}.pdf\"')
        ])
