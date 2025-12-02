from odoo import models, fields, api


class HrEmployeeJobHistory(models.Model):
    _name = 'hr.employee.job.history'
    _description = 'Historial de Cambios de Puesto'
    _order = 'change_date desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Empleado",
        required=True,
        ondelete="cascade"
    )


    old_job_id = fields.Many2one(
        'hr.job',
        string="Puesto Anterior"
    )

    new_job_id = fields.Many2one(
        'hr.job',
        string="Nuevo Puesto"
    )

    change_date = fields.Datetime(
        string="Fecha de Cambio",
        default=fields.Datetime.now
    )

    changed_by = fields.Many2one(
        'res.users',
        string="Modificado por",
        default=lambda self: self.env.user
    )

    job_history_ids = fields.One2many(
        'hr.employee.job.history',
        'employee_id',
        string="Historial de puestos",
        store=True
    )

