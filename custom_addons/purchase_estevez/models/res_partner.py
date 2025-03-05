from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)
import re

class ResPartner(models.Model):
    _inherit = "res.partner"
    nuevo_campo = fields.Char(string="Nombre comercial")       
    email = fields.Char(required=True)
    vat = fields.Char(string="RFC", required=True)
    street = fields.Char(required=True)
    street2 = fields.Char(required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one('res.country.state', required=True)  # Estado
    zip = fields.Char(required=True)  #Codigo Postal
    country_id = fields.Many2one('res.country', required=True)       
    buyer_id = fields.Many2one('hr.employee', string="Comprador", domain="[('department_id', '=', 4)]")  
    #contacto = fields.Char(string="Contacto")       
 # Método para el botón "Guardar"
    def action_guardar(self):
        self.ensure_one()        
        return {
            "type": "ir.actions.act_window_close",
        }

    def action_open_whatsapp(self):
        for partner in self:  # Cambia 'applicant' a 'partner' ya que es res.partner
            if partner.phone:
                phone = re.sub(r'\D', '', partner.phone)
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Que tal!"
                url = f"https://wa.me/{phone}?text={message}"
                _logger.info(f"Opening WhatsApp: {url}")
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("El contacto no tiene un número de teléfono.")

                # Restricción para asegurar que el código sea único
    _sql_constraints = [
        ('rfc_unique', 'UNIQUE(vat)', 'El RFC ya existe.'),
    ]

    