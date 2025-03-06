from odoo import models, fields

class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    clabe = fields.Char(string="Clabe")
    reference = fields.Char(string="Referencia")
    acc_holder_name = fields.Char(string="Titular")