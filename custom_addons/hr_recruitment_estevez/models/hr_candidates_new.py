from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HRCandidate(models.Model):
    _inherit = 'hr.candidate'

    first_name = fields.Char(string='Nombre(s)')
    last_name = fields.Char(string='Apellido paterno')
    mother_last_name = fields.Char(string='Apellido materno')

    @api.onchange('first_name', 'last_name', 'mother_last_name')
    def _onchange_fill_partner_name(self):
        # Construir partner_name con los tres campos separados
        parts = filter(None, [self.first_name, self.last_name, self.mother_last_name])
        self.partner_name = ' '.join(parts)

    @api.model
    def create(self, vals):
        # Si no se asigna partner_id, y hay partner_name, crea un res.partner automáticamente
        if not vals.get('partner_id') and vals.get('partner_name'):
            partner = self.env['res.partner'].create({
                'name': vals['partner_name'],
            })
            vals['partner_id'] = partner.id
        return super().create(vals)

    def write(self, vals):
        # También cubrir el caso en edición si se elimina partner_id
        for record in self:
            if not vals.get('partner_id') and vals.get('partner_name') and not record.partner_id:
                partner = self.env['res.partner'].create({
                    'name': vals['partner_name'],
                })
                vals['partner_id'] = partner.id
        return super().write(vals)


    def action_save(self):
        # Aquí puedes agregar cualquier lógica adicional antes de guardar
        self.ensure_one()        
        _logger.info("Requisición guardada con éxito")
        # Crear acción de retorno
        action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'current',
        }
        
        return {
        'effect': {
            'type': 'rainbow_man',
            'message': '¡Requisición completada exitosamente!',
            'fadeout': 'slow',
            'next': {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'list',      # Cambiado a vista de tabla
                'views': [(False, 'list')],
                'target': 'current'                       
                
            }
        }
    }




