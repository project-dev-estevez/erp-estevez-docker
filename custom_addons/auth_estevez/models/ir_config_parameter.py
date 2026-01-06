from odoo import models, api
from odoo.tools import ormcache

class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    @ormcache('key')
    def get_param_with_last_update(self, key):
        """Obtiene parámetro del sistema con su fecha de última actualización."""
        self.check_access_rights('read')
        param = self.sudo().search([('key', '=', key)], limit=1)

        if not param:
            return False, False
        
        return param.value, param.write_date
