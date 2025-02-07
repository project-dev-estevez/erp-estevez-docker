from odoo import models, fields

class HrRequisitionEpp(models.Model):
    _name = 'hr.requisition.epp'
    _description = 'Equipo de Protección Personal'

    name = fields.Char(string='Nombre', required=True)