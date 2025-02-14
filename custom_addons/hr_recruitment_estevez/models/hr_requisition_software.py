from odoo import models, fields

class HrRequisitionSoftware(models.Model):
    _name = 'hr.requisition.software'
    _description = 'Software que se utilizará por el empleado'

    name = fields.Char(string='Nombre', required=True)