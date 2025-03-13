from odoo import models, api
import base64  # Importa la librería base64

class IrActionsReport(models.AbstractModel):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # Render the PDF
        pdf_content, report_type = super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids, data)

        # Get the report and model
        report = self._get_report(report_ref)
        model = report.model
        records = self.env[model].browse(res_ids)

        # Save the PDF as an attachment with a fixed name
        for record in records:
            attachment_name = "Historia Clínica"  # Nombre fijo

            # Buscar si ya existe un archivo adjunto con el mismo nombre
            existing_attachment = self.env['ir.attachment'].search([
                ('name', '=', attachment_name),
                ('res_model', '=', model),
                ('res_id', '=', record.id),
            ], limit=1)

            # Si existe, eliminarlo
            if existing_attachment:
                existing_attachment.unlink()

            # Crear el nuevo archivo adjunto
            self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),  # Codifica el contenido del PDF en base64
                'res_model': model,
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })

        return pdf_content, report_type