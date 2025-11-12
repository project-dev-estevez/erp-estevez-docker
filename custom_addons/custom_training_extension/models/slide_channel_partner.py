from odoo import models, fields, api

class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_employee_elearning_report()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_employee_elearning_report()
        return res

    def _sync_employee_elearning_report(self):
        """Actualiza automáticamente la tabla employee.elearning.report"""
        Report = self.env['employee.elearning.report']

        for rec in self:
            # Buscar empleado asociado
            employee = self.env['hr.employee'].search([
                '|',
                ('user_id.partner_id', '=', rec.partner_id.id),
                ('work_contact_id', '=', rec.partner_id.id)
            ], limit=1)

            if not employee or not rec.channel_id:
                continue

            existing = Report.search([
                ('employee_id', '=', employee.id),
                ('course_id', '=', rec.channel_id.id)
            ], limit=1)

            values = {
                'employee_id': employee.id,
                'course_id': rec.channel_id.id,
                'date_completed': getattr(rec, 'completed_on', False) or getattr(rec, 'completed_date', False) or False,
                'completion': rec.completion,
                'channel_type': rec.channel_id.channel_type,
                'modalidad': getattr(rec.channel_id, 'modalidad', 'Presencial'),
            }

            if existing:
                existing.write(values)
            else:
                Report.create(values)
