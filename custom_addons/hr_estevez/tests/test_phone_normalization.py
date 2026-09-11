# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.hr_estevez.models.hr_employee import normalize_mx_phone


class TestPhoneNormalization(TransactionCase):
    """Normalización de teléfonos e independencia work_phone / private_phone."""

    def test_normalize_mx_10_digits(self):
        self.assertEqual(normalize_mx_phone('5616102081'), '+52 561 610 2081')

    def test_normalize_strips_symbols(self):
        self.assertEqual(normalize_mx_phone('(561) 610-2081'), '+52 561 610 2081')
        self.assertEqual(normalize_mx_phone('tel. 561 610 2081'), '+52 561 610 2081')

    def test_normalize_with_52_prefix(self):
        self.assertEqual(normalize_mx_phone('+525616102081'), '+52 561 610 2081')
        self.assertEqual(normalize_mx_phone('52 561 610 2081'), '+52 561 610 2081')

    def test_normalize_is_idempotent(self):
        once = normalize_mx_phone('5616102081')
        self.assertEqual(normalize_mx_phone(once), once)

    def test_normalize_foreign_number_untouched(self):
        self.assertEqual(normalize_mx_phone('+1 202 555 0143'), '+1 202 555 0143')

    def test_normalize_falsy_values(self):
        self.assertIs(normalize_mx_phone(False), False)
        self.assertIs(normalize_mx_phone(None), None)
        self.assertEqual(normalize_mx_phone('   '), '')

    def test_create_write_keep_phones_independent_and_formatted(self):
        with patch.object(
            type(self.env['hr.employee']), '_sync_codeigniter', return_value=(True, '')
        ):
            employee = self.env['hr.employee'].create({
                'names': 'Empleado',
                'last_name': 'Test',
                'mother_last_name': 'Telefonos',
                'marital': 'single',
                'work_phone': '5544332211',
                'private_phone': '5616102081',
            })
            self.assertEqual(employee.work_phone, '+52 554 433 2211')
            self.assertEqual(employee.private_phone, '+52 561 610 2081')

            employee.write({'private_phone': '5599887766'})
            # private_phone se actualiza y normaliza; work_phone NO se toca.
            self.assertEqual(employee.private_phone, '+52 559 988 7766')
            self.assertEqual(employee.work_phone, '+52 554 433 2211')
