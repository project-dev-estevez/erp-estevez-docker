from odoo import models

class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    def generate_course_certificate(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar Certificado',
            'res_model': 'certificate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_elearning_integration.view_certificate_wizard_form').id,
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_course_id': self.id,
            },
        }
