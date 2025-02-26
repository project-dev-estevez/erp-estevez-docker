# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name": "Applicant Document Management",
    "version": "18.0.0.0",
    "category": "Human Resources",
    'summary': "Applicant Document Access Candidate Documents Applicant Attached Document Management Multiple Document Attachments for Applicant Upload Document Candidate Document Attachment Download Documents for Recruitment Applicant Document Job Applicant Document",
    "description": """
    
        Applicant Document Management Odoo App helps users to view and manage all attached documents on an application with smart button in the form view that showing the number of the document attached. All attached documents on an applicants are available and viewed in tree view, form view and kanban view. Users can also download attachments easily from it.
    
    """,
    'author': 'BROWSEINFO',
    'website': "https://www.browseinfo.com/demo-request?app=bi_applicant_document_management&version=18&edition=Community",
    "depends": ['base', 'hr_recruitment'],
    "data": [
        'views/hr_applicant_views.xml',
        'views/ir_attachment_views.xml',
        ],
    'license':'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url':'https://www.browseinfo.com/demo-request?app=bi_applicant_document_management&version=18&edition=Community',
    "images":['static/description/Applicant-Document-Management-Banner.gif'],
}
