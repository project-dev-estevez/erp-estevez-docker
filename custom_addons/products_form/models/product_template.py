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

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Moneda",
        domain="[('name', 'in', ['MXN', 'USD'])]",  # Filtra solo MXN y USD
        default=lambda self: self.env.ref('base.MXN').id,
    )

    # Restricción para asegurar que el código sea único
    _sql_constraints = [
        ('codigo_unique', 'UNIQUE(codigo)', 'El código debe ser único.'),
    ]