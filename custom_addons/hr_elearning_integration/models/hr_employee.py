from odoo import models, fields, api

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    course_ids = fields.Many2many(
        comodel_name='slide.channel',
        string='Cursos Inscritos',
        compute='_compute_course_ids',
        store=False
    )

    @api.depends('user_id.partner_id')
    def _compute_course_ids(self):
        """Computa los cursos sin depender de otros módulos"""
        SlideChannelPartner = self.env['slide.channel.partner']
        for employee in self:
            if employee.user_id and employee.user_id.partner_id:
                partner_id = employee.user_id.partner_id.id
                channel_partners = SlideChannelPartner.search([
                    ('partner_id', '=', partner_id)
                ])
                employee.course_ids = channel_partners.mapped('channel_id')
            else:
                employee.course_ids = False