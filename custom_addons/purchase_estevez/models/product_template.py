from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"


    barcode = fields.Char(
        string="Barcode",
        store=False,  # No se almacena en la base de datos
    )

    taxes_id = fields.Many2many(
        comodel_name='account.tax',
        string="Impuestos",
        related=False,  # Desvincula el campo heredado
        store=False,    # No almacena en la base de datos
    )

    # Nuevo campo "codigo"
    codigo = fields.Char(
        string="Código",
        index=True,
        help="Código único para identificar el producto.",
        copy=False,  # No copiar el valor al duplicar el producto
        tracking=True,  # Registrar cambios en el chatter
    )

    # Nuevo campo "modelo"
    model = fields.Char(
        string="Modelo",
        help="Modelo.",
        copy=False,  # No copiar el valor al duplicar el producto
    )

    # Nuevo campo "marca"
    marca = fields.Char(
        string="Marca",
        help="Marca.",
        copy=False,  # No copiar el valor al duplicar el producto
    )

    # Nuevo campo "marca"
    description = fields.Char(
        string="Descripcion",
        help="Descripcion.",
        copy=False,  # No copiar el valor al duplicar el producto
    )

    # Campo Many2one hacia res.currency (monedas disponibles)
    custom_currency_id = fields.Many2one(
        'res.currency',
        string="Moneda Personalizada",
        help="Selecciona una moneda para este producto.",
        domain="[('active', '=', True)]"  # Filtra solo monedas activas
    )

    # Campo Many2one hacia unidades de medida (uom.uom)
    custom_uom_id = fields.Many2one(
        'uom.uom',  # Modelo de unidades de medida en Odoo 18
        string="Unidad de Medida Personalizada",
        help="Selecciona una unidad de medida para este producto.",
        domain="[('active', '=', True)]"  # Solo unidades activas
    )
    
   

    # Restricción para asegurar que el código sea único
    _sql_constraints = [
        ('codigo_unique', 'UNIQUE(codigo)', 'El código debe ser único.'),
    ]

     # Campo computado para el último costo
    last_cost = fields.Float(
        string="Último Costo Registrado",
        compute="_compute_last_cost",
        store=False,  # No almacenado en BD (se calcula en tiempo real)
        help="Último costo registrado desde compras o inventario."
    )

    @api.depends()
    def _compute_last_cost(self):
        for product in self:
            # Buscar el último movimiento de inventario de tipo "entrada" para el producto
            stock_move = self.env['stock.move'].search([
                ('product_id', '=', product.product_variant_id.id),
                ('picking_code', '=', 'incoming'),  # Movimientos de entrada
                ('state', '=', 'done')  # Movimientos completados
            ], order='date desc', limit=1)

            if stock_move:
                product.last_cost = stock_move.price_unit
            else:
                # Si no hay movimientos, buscar en las órdenes de compra
                purchase_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', product.product_variant_id.id),
                    ('state', '=', 'purchase')  # Órdenes de compra confirmadas
                ], order='date_order desc', limit=1)

                product.last_cost = purchase_line.price_unit if purchase_line else 0.0