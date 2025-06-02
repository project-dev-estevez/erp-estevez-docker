from odoo import models, fields, api
from odoo.exceptions import UserError

class HrJob(models.Model):
    _inherit = 'hr.job'

    requisition_id = fields.Many2one('hr.requisition', string="Requisición Asociada", domain="[('state', '=', 'approved')]")
    is_requisition_required = fields.Boolean(string="¿Requisición Obligatoria?", default=True)

    applicant_ids = fields.One2many(
        'hr.applicant', 'job_id', string='Applicants'
    )

    refused_applicant_count = fields.Integer(
        string='Rechazados',
        compute='_compute_refused_applicant_count'
    )

    in_process_applicant_count = fields.Integer(
        string='En Proceso',
        compute='_compute_in_process_applicant_count'
    )

    @api.depends()
    def _compute_refused_applicant_count(self):
        for job in self:
            count = self.env['hr.applicant'].search_count([
                ('job_id', '=', job.id),
                ('active', '=', False),
                ('refuse_reason_id', '!=', False),
            ])
            job.refused_applicant_count = count

    @api.depends()
    def _compute_in_process_applicant_count(self):
        for job in self:
            count = self.env['hr.applicant'].search_count([
                ('job_id', '=', job.id),
                ('application_status', 'not in', ['refused', 'hired']),
            ])
            job.in_process_applicant_count = count

    @api.model
    def create(self, vals):
        if self.is_requisition_required and not vals.get('requisition_id'):
            raise UserError("No puedes crear una vacante sin una requisición aprobada.")
        return super(HrJob, self).create(vals)