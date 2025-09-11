import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class HrInstructores(models.Model):
    _name = 'hr.instructores'
    _description = 'Catálogo de Instructores'

    name = fields.Char(string="Nombre", required=True)
    tipo = fields.Selection([
        ('interno', 'Interno'),
        ('externo', 'Externo'),        
    ], string='Tipo de Instructor')

    def action_save(self):
        self.ensure_one()

        _logger.info("Mostrando vista lista + efecto rainbow_man")

        return {
            'effect': { 
                'fadeout': 'slow',
                'message': '¡Instructor registrado exitosamente!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'res_model': self._name, 
            'view_mode': 'list',
            'target': 'current',
            
        }
