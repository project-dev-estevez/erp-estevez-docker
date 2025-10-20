from odoo import fields, models

class HrLeaveType(models.Model):
    """This module inherits from the 'hr.leave.type' model of the Odoo Time Off
    Module. It adds a new field called 'leave_code', which is a selection field
    that allows users to choose from a list of predefined leave codes."""
    _inherit = 'hr.leave.type'

    leave_code = fields.Selection(
        [
            ('UL', 'LSGS'),  # Licencia sin goce de sueldo
            ('SL', 'LPE'),   # Licencia por enfermedad
            ('RL', 'LR'),    # Licencia regular
            ('NL', 'LN'),    # Licencia normal
            ('ML', 'LM'),    # Licencia de maternidad
            ('FL', 'LF'),    # Licencia por festividad
            ('CL', 'LC'),    # Licencia compensatoria
            ('PL', 'LGS'),   # Licencia con goce de sueldo
            ('OL', 'LO'),    # Otra licencia
        ],
        required=True,
        string="Código de Licencia",
        default="NL",
        help="LSGS = Licencia sin goce de sueldo\n"
             "LPE = Licencia por enfermedad\n"
             "LR = Licencia regular\n"
             "LN = Licencia normal\n"
             "LM = Licencia de maternidad\n"
             "LF = Licencia por festividad\n"
             "LC = Licencia compensatoria\n"
             "LGS = Licencia con goce de sueldo\n"
             "LO = Otra licencia")
