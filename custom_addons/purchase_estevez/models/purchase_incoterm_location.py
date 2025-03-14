from odoo import models, fields, api

class IncotermLocation(models.Model):
    _name = "purchase.incoterm.location"
    _description = "Ubicaciones para Incoterms"
    
    name = fields.Char(string="Nombre", required=True)