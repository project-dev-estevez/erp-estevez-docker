# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestContractRules(TransactionCase):
    """Un contrato nuevo solo se crea si el actual está cancelado, y los nombres
    automáticos son "Contrato Inicial", "Contrato N" y "Contrato Final"."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, skip_codeigniter_sync=True, tracking_disable=True))
        cls.today = fields.Date.today()
        cls.employee = cls.env['hr.employee'].create({
            'names': 'Reglas', 'last_name': 'Prueba', 'mother_last_name': 'Contrato',
            'employee_number': 'REGLA001', 'barcode': 'REGLA001',
        })
        ContractType = cls.env['hr.contract.type']
        cls.type_fixed = ContractType.create({'name': 'Determinado'})
        cls.type_indefinite = ContractType.create({'name': 'Indeterminado'})

    def _contract(self, **vals):
        return self.env['hr.contract'].create(dict({
            'name': 'x', 'employee_id': self.employee.id, 'wage': 1000,
            'date_start': self.today, 'contract_type_id': self.type_fixed.id,
        }, **vals))

    def test_names_and_creation_rule(self):
        first = self._contract(date_end=self.today + timedelta(days=90))
        self.assertEqual(first.name, 'Contrato Inicial')
        self.assertEqual(first.state, 'open')

        # En proceso: no se puede crear otro
        with self.assertRaises(UserError):
            self._contract()

        first.action_cancel_contract()
        second = self._contract(date_end=self.today + timedelta(days=180))
        self.assertEqual(second.name, 'Contrato 2')

        # Al marcarlo indeterminado pasa a ser el contrato final
        second.contract_type_id = self.type_indefinite
        self.assertEqual(second.name, 'Contrato Final')
        second.contract_type_id = self.type_fixed
        self.assertEqual(second.name, 'Contrato 2')

        second.action_cancel_contract()
        final = self._contract(contract_type_id=self.type_indefinite.id)
        self.assertEqual(final.name, 'Contrato Final')

    def test_expired_contract_blocks_until_cancelled(self):
        expired = self._contract(date_start=self.today - timedelta(days=200),
                                 date_end=self.today - timedelta(days=10))
        self.assertEqual(expired.state, 'close')
        with self.assertRaises(UserError):
            self._contract()
        expired.action_cancel_contract()
        self.assertEqual(self._contract().name, 'Contrato 2')

    def test_manual_name_is_kept(self):
        contract = self._contract()
        contract.name = 'Contrato especial'
        contract.contract_type_id = self.type_indefinite
        self.assertEqual(contract.name, 'Contrato especial')

    def test_form_name_follows_contract_type(self):
        form = Form(self.env['hr.contract'].with_context(default_employee_id=self.employee.id))
        self.assertEqual(form.name, 'Contrato Inicial')
        form.contract_type_id = self.type_indefinite
        self.assertEqual(form.name, 'Contrato Final')
        form.contract_type_id = self.type_fixed
        self.assertEqual(form.name, 'Contrato Inicial')

    def test_new_form_blocked_while_contract_running(self):
        self._contract()
        with self.assertRaises(UserError):
            Form(self.env['hr.contract'].with_context(default_employee_id=self.employee.id))
