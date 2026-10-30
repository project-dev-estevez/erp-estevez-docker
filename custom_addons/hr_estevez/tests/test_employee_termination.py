# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestEmployeeTermination(TransactionCase):
    """Al dar de baja a un empleado sus contratos en curso o en borrador se cancelan."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, skip_codeigniter_sync=True, tracking_disable=True))
        cls.today = fields.Date.today()
        cls.counter = 0

    def _employee_with_contracts(self):
        self.__class__.counter += 1
        n = self.counter
        employee = self.env['hr.employee'].create({
            'names': f'Baja {n}', 'last_name': 'Prueba', 'mother_last_name': 'Contrato',
            'employee_number': f'BAJA{n:03d}', 'barcode': f'BAJA{n:03d}',
        })
        # hr.contract.create fija el estado según la fecha de fin (vencido → close, si no → open),
        # así que el borrador se crea antes que el vigente y se pasa a draft
        Contract = self.env['hr.contract']
        expired = Contract.create({'name': 'Vencido', 'employee_id': employee.id, 'wage': 1000,
                                   'date_start': self.today - timedelta(days=400),
                                   'date_end': self.today - timedelta(days=40)})
        draft = Contract.create({'name': 'Borrador', 'employee_id': employee.id, 'wage': 1000,
                                 'date_start': self.today + timedelta(days=30)})
        draft.state = 'draft'
        running = Contract.create({'name': 'Vigente', 'employee_id': employee.id, 'wage': 1000,
                                   'date_start': self.today - timedelta(days=30)})
        self.assertEqual((expired.state, draft.state, running.state), ('close', 'draft', 'open'))
        return employee, expired, running, draft

    def test_wizard_termination_cancels_contracts(self):
        employee, expired, running, draft = self._employee_with_contracts()
        wizard = self.env['hr.employee.archive.wizard'].create({
            'employee_id': employee.id,
            'termination_type': 'voluntary_resignation',
            'reason': 'Prueba',
        })
        wizard.confirm_archive()
        self.assertFalse(employee.active)
        self.assertEqual(running.state, 'cancel')
        self.assertEqual(draft.state, 'cancel')
        # Un contrato ya vencido se queda como estaba
        self.assertEqual(expired.state, 'close')

    def test_direct_archive_cancels_contracts(self):
        employee, _expired, running, _draft = self._employee_with_contracts()
        employee.action_archive()
        self.assertEqual(running.state, 'cancel')

    def test_other_writes_do_not_touch_contracts(self):
        employee, _expired, running, _draft = self._employee_with_contracts()
        employee.write({'private_street': 'Calle Prueba'})
        employee.write({'active': True})
        self.assertEqual(running.state, 'open')
