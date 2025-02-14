from odoo import models, fields

class ResPartnerIndustry(models.Model):
    _inherit = "res.partner.industry"

    # Aquí puedes agregar campos adicionales si lo necesitas
    custom_code = fields.Char(string="Código personalizado")