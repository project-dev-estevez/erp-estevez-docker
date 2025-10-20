from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    """Esta clase extiende `res.config.settings` para agregar configuraciones
    del dashboard de asistencias de RRHH para los símbolos por defecto de presente y ausente."""
    _inherit = 'res.config.settings'

    present = fields.Selection(
        [
            ('present', 'Presente'),
            ('\u2714', '✔'), 
            ('\u2705', '✅'), 
            ('p', 'P')
        ],
        string='Marca por defecto para Presente',
        config_parameter='advance_hr_attendance_dashboard.present',
        help='Selecciona la marca por defecto para asistencia presente.'
    )

    absent = fields.Selection(
        [
            ('absent', 'Ausente'),
            ('\u2716', '✘'),
            ('\u274C', '❌'),
            ('\u2B55', '⭕'),
            ('a', 'A')
        ],
        string='Marca por defecto para Ausente',
        config_parameter='advance_hr_attendance_dashboard.absent',
        help='Selecciona la marca por defecto para asistencia ausente.'
    )