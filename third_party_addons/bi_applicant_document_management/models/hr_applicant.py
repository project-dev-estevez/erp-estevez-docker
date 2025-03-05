# -*- coding: utf-8 -*-
from odoo import fields, models, _

class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    documents_count = fields.Integer(
        'Documents Count', compute="_compute_applicant_documents")

    required_documents = fields.Char(
        'Required Documents', compute="_compute_required_documents")

    def _compute_applicant_documents(self):
        for record in self:
            record.documents_count = self.env['ir.attachment'].search_count(
                [('res_model', '=', 'hr.applicant'), ('res_id', '=', record.id)])

    def _compute_required_documents(self):
        required_documents = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        for record in self:
            record.required_documents = ', '.join(required_documents)

    def action_open_documents(self):
        required_documents = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        return {
            'name': _('Documentos del Aplicante'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'view_id': self.env.ref('bi_applicant_document_management.view_hr_applicant_documents').id,
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'hr.applicant'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'hr.applicant',
                'default_res_id': self.id,
                'required_documents': required_documents,
            },
        }