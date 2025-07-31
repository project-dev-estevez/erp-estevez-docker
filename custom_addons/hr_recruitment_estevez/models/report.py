from odoo import models, api
import base64

class IrActionsReport(models.AbstractModel):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        pdf_content, report_type = super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids, data)
        report = self._get_report(report_ref)
        model = report.model
        records = self.env[model].browse(res_ids)

        for record in records:
            # Refinar condicionales para cada tipo de reporte
            if report_ref == 'hr_recruitment_estevez.hr_applicant_driving_test_report_document':
                attachment_name = "Evidencia prueba de manejo"
            elif report_ref == 'hr_recruitment_estevez.report_hr_applicant_document':
                attachment_name = "Historia Clínica"
            else:
                continue

            existing_attachment = self.env['ir.attachment'].search([
                ('name', '=', attachment_name),
                ('res_model', '=', model),
                ('res_id', '=', record.id),
            ], limit=1)
            if existing_attachment:
                existing_attachment.unlink()

            self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': model,
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })

        return pdf_content, report_type