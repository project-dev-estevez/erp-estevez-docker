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

    is_published = fields.Boolean(
        string='Publicado',
        tracking=True
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
    
    def write(self, vals):
        # Si estamos en contexto de actualización desde requisición, saltar
        if self.env.context.get('skip_requisition_update'):
            return super(HrJob, self).write(vals)
            
        # Verificar si estamos cambiando el campo is_published
        if 'is_published' in vals:
            for job in self:
                # Buscar requisiciones relacionadas
                requisitions = self.env['hr.requisition'].search([
                    ('workstation_job_id', '=', job.id),
                    ('state', '=', 'approved')
                ])
                
                # Ejecutar la acción correspondiente en las requisiciones
                if vals['is_published']:
                    requisitions.action_publish_vacancy(from_job=True)
                else:
                    requisitions.action_close_vacancy(from_job=True)
        
        return super(HrJob, self).write(vals)