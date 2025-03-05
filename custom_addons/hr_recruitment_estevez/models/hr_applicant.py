from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    documents_count = fields.Integer(
        'Documents Count', compute="_compute_applicant_documents")
    
    def _compute_applicant_documents(self):
        for record in self:
            record.documents_count = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'hr.applicant'), ('res_id', '=', record.id)])
    
    def action_open_documents(self):
        required_documents = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        return {
            'name': _('Documentos del Aplicante'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'view_id': self.env.ref('hr_recruitment_estevez.view_hr_applicant_documents').id,
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'hr.applicant'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'hr.applicant',
                'default_res_id': self.id,
                'required_documents': required_documents,
            },
        }

    def _format_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+52'):
            phone_number = '+52 ' + re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1 \2 \3', phone_number)
        return phone_number

    @api.onchange('partner_phone')
    def _onchange_partner_phone(self):
        if self.partner_phone:
            self.partner_phone = self._format_phone_number(self.partner_phone)

    def action_open_whatsapp(self):
        for applicant in self:
            if applicant.partner_phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', applicant.partner_phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola"
                url = f"https://wa.me/{phone}?text={message}"
                _logger.info(f"Opening WhatsApp with phone number: {phone}")
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("The applicant does not have a phone number.")