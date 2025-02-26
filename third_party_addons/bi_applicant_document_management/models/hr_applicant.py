# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, _


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    documents_count = fields.Integer(
        'Documents Count', compute="_compute_applicant_documents")

    def _compute_applicant_documents(self):
        for record in self:
            record.documents_count = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'hr.applicant'), ('res_id', '=', record.id)])

    def action_open_documents(self):
        return {
            'name': _('Documentos del solicitante'),
            'view_type': 'form',
            'view_mode': 'kanban,list,form',
            'res_model': 'ir.attachment',
            'view_id': self.env.ref('bi_applicant_document_management.view_ir_attachment_kanban').id,  # Especificar la vista kanban
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'hr.applicant'), ('res_id', '=', self.id)],
            'context': {'default_res_model': 'hr.applicant', 'default_res_id': self.id},
        }
