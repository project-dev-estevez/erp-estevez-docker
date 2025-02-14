from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"
    nuevo_campo = fields.Char(string="Nombre comercial")
    email = fields.Char(required=True)
    vat = fields.Char(string="RFC", required=True)
    street = fields.Char(required=True)  # Calle
    street2 = fields.Char(required=True)  # Calle 2 (opcional, si también quieres que sea obligatorio)
    city = fields.Char(required=True)  # Ciudad
    state_id = fields.Many2one('res.country.state', required=True)  # Estado
    zip = fields.Char(required=True)  # Código Postal
    country_id = fields.Many2one('res.country', required=True)  # País

       