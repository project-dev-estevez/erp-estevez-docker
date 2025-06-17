from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class HrCandidate(models.Model):
    _inherit = 'hr.candidate'

    rfc = fields.Char(string="RFC")
    job_ids = fields.Many2many(
        'hr.job',
        string = 'Puesto de Trabajo'
    )

    source_id = fields.Many2one(
        'utm.source',
        string='Fuente de Reclutamiento'
    )

    whatsapp_url = fields.Char(
        string='WhatsApp URL',Add commentMore actions
        compute='_compute_whatsapp_url',
        store=False
    )
      
    def action_open_documents(self):
        self.env['hr.applicant.document'].search([]).unlink()
        docs = self.env['hr.applicant.document'].create_required_documents(self.id)

        return {
            'name': _('Documentos del Aplicante'),
            'view_mode': 'kanban',
            'res_model': 'hr.applicant.document',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False},
            'views': [(self.env.ref('hr_recruitment_estevez.view_hr_applicant_documents_kanban').id, 'kanban')],  # Asegúrate de usar la vista correcta
        }
    
    def action_open_whatsapp(self):
        for applicant in self:
            if applicant.partner_phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', applicant.partner_phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola! Estoy interesado en tu perfil para una oportunidad laboral."
                url = f"https://wa.me/{phone}?text={message}"
                _logger.info(f"Opening WhatsApp with phone number: {phone}")
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("The applicant does not have a phone number.")
                
    
    def action_open_whatsapp(self):
        for applicant in self:
            if applicant.partner_phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', applicant.partner_phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola, estoy interesado en tu perfil para una oportunidad laboral."
                url = f"https://wa.me/{phone}?text={message}"
                _logger.info(f"Opening WhatsApp with phone number: {phone}")
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("The applicant does not have a phone number.")

    def _format_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+52'):
            phone_number = '+52 ' + re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1 \2 \3', phone_number)
        return phone_number

    @api.onchange('partner_phone')
    def _onchange_partner_phone(self):
        if self.partner_phone:
            self.partner_phone = self._format_phone_number(self.partner_phone)

    #def action_open_whatsapp(self):
        #for candidate in self:
            #if candidate.partner_phone:
                # Eliminar caracteres no numéricos
                #phone = re.sub(r'\D', '', candidate.partner_phone)
                # Verificar si el número ya tiene un código de país
                #if not phone.startswith('52'):
                    #phone = '52' + phone
                #message = "Hola"
                #url = f"https://wa.me/{phone}?text={message}"
                #_logger.info(f"Opening WhatsApp with phone number: {phone}")
                #return {
                    #'type': 'ir.actions.act_url',
                    #'url': url,
                    #'target': 'new',
                #}
            #else:
                #raise UserError("The candidate does not have a phone number.")      

    @api.model
    def create(self, vals):
        if vals.get('rfc'):
            existing_candidate = self.with_context(active_test=False).search([('rfc', '=', vals['rfc']), ('rfc', '!=', '')], limit=1)
            if existing_candidate:
                # Archivar el candidato existente con el mismo RFC
                existing_candidate.active = False
                raise UserError("El candidato con RFC %s ya se ha postulado anteriormente!" % vals['rfc'])
        return super(HrCandidate, self).create(vals)