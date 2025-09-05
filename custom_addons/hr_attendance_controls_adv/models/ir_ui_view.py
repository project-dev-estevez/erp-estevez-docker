from odoo import fields, models

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[
        ('geofence_view', 'Geofence View')
    ],ondelete={'ganttview': 'cascade'})

    def _get_view_info(self):
        return {'geofence_view': {'icon': 'fa fa-map'}} | super()._get_view_info()