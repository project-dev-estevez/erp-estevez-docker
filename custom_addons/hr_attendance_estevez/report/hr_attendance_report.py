# -*- coding: utf-8 -*-

from odoo import api, models

class ReportHrAttendance(models.AbstractModel):
    """This is an abstract model for the Attendance Report of Employees."""
    _name = 'report.hr_attendance_estevez.report_hr_attendance'
    _description = 'Attendance Report of Employees'

    @api.model
    def _get_report_values(self, doc_ids, data=None):
        """Get the report values for the Attendance Report."""
        return {
            'doc_model': 'hr.attendance',
            'data': data,
            'self': self,
        }
