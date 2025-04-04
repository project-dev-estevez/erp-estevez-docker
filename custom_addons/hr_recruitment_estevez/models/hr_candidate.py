from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class HrCandidate(models.Model):
    _inherit = 'hr.candidate'

    rfc = fields.Char(string="RFC")

    def _format_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+52'):
            phone_number = '+52 ' + re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1 \2 \3', phone_number)
        return phone_number

    @api.onchange('partner_phone')
    def _onchange_partner_phone(self):
        if self.partner_phone:
            self.partner_phone = self._format_phone_number(self.partner_phone)

    def action_open_whatsapp(self):
        for candidate in self:
            if candidate.partner_phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', candidate.partner_phone)
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
                raise UserError("The candidate does not have a phone number.")      

    @api.model
    def create(self, vals):
        if vals.get('rfc'):
            existing_candidate = self.with_context(active_test=False).search([('rfc', '=', vals['rfc']), ('rfc', '!=', '')], limit=1)
            if existing_candidate:
                # Archivar el candidato existente con el mismo RFC
                existing_candidate.active = False
                raise UserError("El candidato con RFC %s ya se ha postulado anteriormente!" % vals['rfc'])
        return super(HrCandidate, self).create(vals)