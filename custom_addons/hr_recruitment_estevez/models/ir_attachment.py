from odoo import models, api

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        # Solo forzar nombre en el flujo explícito de adjuntar documento requerido.
        if self._context.get('force_document_name') and self._context.get('default_name'):
            vals['name'] = self._context.get('default_name')
        return super(IrAttachment, self).create(vals)