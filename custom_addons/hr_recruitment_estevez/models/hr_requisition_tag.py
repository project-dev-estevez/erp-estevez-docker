from odoo import models, fields

class HrRequisitionTag(models.Model):
    _name = 'hr.requisition.tag'
    _description = 'HR Requisition Tag'

    name = fields.Char(string='Tag Name', required=True)