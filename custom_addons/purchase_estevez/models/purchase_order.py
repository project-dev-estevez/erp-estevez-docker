from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


    incoterm_location_id = fields.Many2one(
        'purchase.incoterm.location',
        string="Ubicación Incoterm",
        help="Seleccione la ubicación asociada al Incoterm."
    )