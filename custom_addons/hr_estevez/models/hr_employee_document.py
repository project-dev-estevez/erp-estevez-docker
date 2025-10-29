from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployeeDocument(models.Model):
    _name = 'hr.employee.document'
    _description = 'Documentos requeridos para el empleado'

    name = fields.Char(string="Nombre del Documento", required=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True)
    attached = fields.Boolean(string="Adjunto", compute="_compute_attached", store=True)

    @api.depends('name', 'employee_id')
    def _compute_attached(self):
        for record in self:
            existing_docs = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.employee'),
                ('res_id', '=', record.employee_id.id),
                ('name', '=', record.name)
            ])
            record.attached = bool(existing_docs)

    @api.model
    def create_required_documents(self, employee_id):
        required_documents = [
            'INE Frente/Reverso',
            'INE Reverso',
            'Curriculum',
            'Acta de Nacimiento',
            'Comprobante de estudios',
            'Comprobante de domicilio',
            'Comprobante Número de Seguridad Social',
            'Formato RFC',
            'Licencia de Conducir',
            'Cartas de Recomendacion Laboral',
            'Carta de Recomendacion Personal',
            'Carta de retencion Infonavit',
            'CURP',
            'Prueba Psicométrica',
            'Historia Clínica',
            'Solicitud de empleo',
            'Anexo G - Aviso de Privacidad de Candidatos',
            'Cuestionario de Salud',
            'Constancia de semanas cotizadas en el IMSS',
            'Constancia de situación fiscal (SAT)',
            'Cuenta Bancaria',
            'Carta de retención de FONACOT',
            'Referencias personales/laborales',
            'Evidencia prueba de manejo',
            'Acuse Kit de contratación',
        ]
        docs_data = []
        for doc_name in required_documents:
            docs_data.append({
                'name': doc_name,
                'employee_id': employee_id,
            })
        return self.create(docs_data)

    def action_attach_document(self):
        self.ensure_one()
        existing_attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', self.employee_id.id),
            ('name', '=', self.name)
        ], limit=1)
        if existing_attachment:
            existing_attachment.unlink()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_estevez.view_attachment_form_custom').id if self.env.ref('hr_estevez.view_attachment_form_custom', raise_if_not_found=False) else False,
            'target': 'new',
            'name': 'Adjunte el Documento',
            'context': {
                'default_res_model': 'hr.employee',
                'default_res_id': self.employee_id.id,
                'default_name': self.name
            },
        }

    def action_view_document(self):
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', self.employee_id.id),
            ('name', '=', self.name)
        ], limit=1)
        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=false',
            'target': 'new',
        }

    def action_download_document(self):
        self.ensure_one()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.employee'),
            ('res_id', '=', self.employee_id.id),
            ('name', '=', self.name)
        ], limit=1)
        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
