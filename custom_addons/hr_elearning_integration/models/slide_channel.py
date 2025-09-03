from odoo import models

class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def generate_course_certificate(self):
        return self.env.ref('hr_elearning_integration.action_report_course_certificate').report_action(self)
