from odoo import models, fields, api
from odoo.exceptions import UserError


class HrEmployeeJobChangeWizard(models.TransientModel):
    _name = 'hr.employee.job.change.wizard'
    _description = 'Registrar cambio manual de puesto'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Empleado",
        required=True
    )

    old_job_id = fields.Many2one(
        'hr.job',
        string="Puesto anterior",
        readonly=True
    )

    new_job_id = fields.Many2one(
        'hr.job',
        string="Nuevo puesto",
        required=True
    )

    start_date = fields.Date(
        string="Fecha de inicio",
        required=True,
        default=fields.Date.context_today
    )

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id:
            self.old_job_id = self.employee_id.job_id.id

    def action_confirm_change(self):
        self.ensure_one()

        self.env['hr.employee.job.history'].create({
            'employee_id': self.employee_id.id,
            'old_job_id': self.old_job_id.id,
            'new_job_id': self.new_job_id.id,
            'start_date': self.start_date,
        })
