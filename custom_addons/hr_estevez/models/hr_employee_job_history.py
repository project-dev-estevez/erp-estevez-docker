from odoo import models, fields, api
from odoo.exceptions import UserError


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

    company_id = fields.Many2one(
        related='employee_id.company_id',
        string="Empresa",
        store=True,
        readonly=True
    )

    start_date = fields.Date(
        string="Fecha de inicio",
        required=True,
        default=fields.Date.context_today
    )

    end_date = fields.Date(
        string="Fecha de fin"
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



    @api.depends('new_job_id')
    def _compute_job_name(self):
        for record in self:
            record.job_name = record.new_job_id.name if record.new_job_id else False     

    def action_attach_file(self):
        self.ensure_one()

        existing_attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if existing_attachment:
            existing_attachment.unlink()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Adjuntar Archivo',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_name': f"Historial_{self.id}",
            },
        }

    def action_view_file(self):
        self.ensure_one()

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")

        preview_view = self.env.ref('hr_estevez.attachment_preview')

        return {
            'type': 'ir.actions.act_window',
            'name': f'Vista previa - {self.employee_id.name}',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'views': [(preview_view.id, 'form')],
            'target': 'new',
        }

    def action_download_file(self):
        self.ensure_one()

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ], limit=1)

        if not attachment:
            raise UserError("No se encontró el archivo adjunto.")

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    @api.model
    def create(self, vals):
        employee_id = vals.get('employee_id')
        start_date = vals.get('start_date') or fields.Date.context_today(self)

        if employee_id:
            last_history = self.search([
                ('employee_id', '=', employee_id),
                ('end_date', '=', False)
            ], order='start_date desc', limit=1)

            if last_history:
                last_history.end_date = start_date

        return super().create(vals)

