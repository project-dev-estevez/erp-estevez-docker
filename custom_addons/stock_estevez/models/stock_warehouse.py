from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
import re


class StockRequisitionLine(models.Model):
    _inherit = 'stock.warehouse'

    type_warehouse = fields.Selection([
        ('general_warehouse', 'Almacén General'),
        ('foreign_warehouse', 'Almacén Foraneo'),
        ('specialized warehouse', 'Almacén Especializado')
    ], string='Tipo Almacén')