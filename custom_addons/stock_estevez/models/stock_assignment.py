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
    serial_number = fields.Char(string="Número de Serie")

    category_type = fields.Selection(
        selection=[
            ('asset', 'Activo Fijo'),
            ('tool', 'Herramienta'),
            ('consumable', 'Consumible'),
        ],
        string='Tipo de Asignación',
        compute='_compute_category_type',
        store=True
    )
    
    @api.depends('product_id.categ_id')
    def _compute_category_type(self):
        for record in self:
            category = record.product_id.categ_id
            try:
                if category == self.env.ref('stock_estevez.category_asset'):
                    record.category_type = 'asset'
                elif category == self.env.ref('stock_estevez.category_tool'):
                    record.category_type = 'tool'
                elif category == self.env.ref('stock_estevez.category_consumable'):
                    record.category_type = 'consumable'
                else:
                    record.category_type = False
            except ValueError:
                # Si las categorías no están instaladas, marca como False
                record.category_type = False