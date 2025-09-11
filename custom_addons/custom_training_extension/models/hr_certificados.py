import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class HrCertificados(models.Model):
    _name = 'hr.certificados'
    _description = 'Catálogo de Certificados'

    code = fields.Char(string="Clave Certificado", required=True)
    description = fields.Char(string="Descripción", required=True)    

    def action_save(self):
        self.ensure_one()

        _logger.info("Mostrando vista lista + efecto rainbow_man")

        return {
            'effect': { 
                'fadeout': 'slow',
                'message': '¡Certificado registrado exitosamente!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'res_model': self._name, 
            'view_mode': 'list',
            'target': 'current',
            
        }
