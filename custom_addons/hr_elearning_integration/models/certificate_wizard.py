from odoo import models, fields, api

class CertificateWizard(models.TransientModel):
    _name = 'certificate.wizard'
    _description = 'Wizard para generar certificado de curso'

    course_id = fields.Many2one('slide.channel', string='Curso', required=True)
    certificate_type = fields.Selection([
        ('participacion', 'Participación'),
        ('aprobacion', 'Aprobación'),
    ], string='Tipo de Certificado', default='participacion', required=True)
    start_date = fields.Date(string='Fecha de Inicio')
    end_date = fields.Date(string='Fecha de Término')
    folio = fields.Char(string='Folio')
    hours = fields.Float(string='Horas del Curso')
    # instructor = fields.Char(string='Instructor')  # Removido
    employer = fields.Char(string='Patrón/Representante')
    workers_rep = fields.Char(string='Representante de Trabajadores')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        course = self.env['slide.channel'].browse(active_id)
        res['course_id'] = course.id
        res['hours'] = course.duration if hasattr(course, 'duration') else 0.0
    # res['instructor'] = course.instructor if hasattr(course, 'instructor') else 'Instructor'  # Removido
        res['employer'] = 'Edwin Gonzalez Soria'
        res['workers_rep'] = 'Jessica Carina Callejas Vazquez'
        return res

    def action_generate_certificate(self):
        # Aquí puedes pasar los datos al reporte usando el contexto o crear un modelo temporal
        return self.env.ref('hr_elearning_integration.action_report_course_certificate').report_action(self.course_id)
