from odoo import models, api

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        # Si se está creando un archivo adjunto desde el contexto de un documento requerido,
        # forzar el nombre del archivo adjunto a ser igual al nombre del documento requerido.
        if 'default_name' in self._context:
            vals['name'] = self._context.get('default_name')
        return super(IrAttachment, self).create(vals)