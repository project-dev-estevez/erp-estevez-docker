from odoo import models, fields

class PurchaseRequisitionService(models.Model):
    _name = 'purchase.requisition.service'
    _description = 'Lista de Servicios'

    name = fields.Char(string='Nombre', required=True)