import logging
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class StockAssignment(models.Model):
    _name = 'stock.assignment'
    _description = 'Asignación de Materiales'

    requisition_id = fields.Many2one('stock.requisition', required=True)
    product_id = fields.Many2one('product.product', string="Producto", required=True)
    quantity = fields.Float(string="Cantidad", required=True)
    recipient_id = fields.Many2one(
        'hr.employee',
        string="Receptor",
        required=True
    )
    assignment_date = fields.Datetime(
        string="Fecha de Asignación",
        default=fields.Datetime.now
    )
    stock_move_id = fields.Many2one('stock.move', string="Movimiento de Inventario")