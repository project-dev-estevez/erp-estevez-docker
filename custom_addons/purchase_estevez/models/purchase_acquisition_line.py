import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

_logger = logging.getLogger(__name__)

class PurchaseAcquisitionLine(models.Model):
    _name = 'purchase.acquisition.line'
    _description = 'Acquisition Line'

    acquisition_id = fields.Many2one('purchase.acquisition', string='Acquisition', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float(string='Unit Price', required=True)
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_price_subtotal', store=True)    

    @api.depends('product_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit