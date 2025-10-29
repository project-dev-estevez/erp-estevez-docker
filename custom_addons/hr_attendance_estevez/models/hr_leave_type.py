from odoo import fields, models

class HrLeaveType(models.Model):
    """This module inherits from the 'hr.leave.type' model of the Odoo Time Off
    Module. It adds a new field called 'code_id', which is a selection field
    that allows users to choose from a list of predefined leave codes."""
    _inherit = 'hr.leave.type'

    code_id = fields.Char(
        string="Código Para Reportes",
        required=True,
        default="*",
        help="Código identificador único para el tipo de licencia."
    )
