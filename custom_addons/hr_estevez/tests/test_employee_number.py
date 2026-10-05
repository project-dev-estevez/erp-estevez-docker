# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestEmployeeNumber(TransactionCase):
    """Número de empleado solo numérico, con rango propio para Kuali."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env['res.company']
        cls.kuali = Company.create({'name': 'Corporativo en Comunicación Digital del Futuro (test)'})
        cls.estevez = Company.create({'name': 'Estevez Test'})

    def _create_employee(self, company, **vals):
        with patch.object(
            type(self.env['hr.employee']), '_sync_codeigniter', return_value=(True, '')
        ):
            return self.env['hr.employee'].with_company(company).create(
                dict({'names': 'Empleado', 'last_name': 'Test', 'company_id': company.id}, **vals)
            )

    def test_kuali_starts_at_300700(self):
        self.assertEqual(self.env['hr.employee']._get_next_employee_number(self.kuali.id), '300700')

    def test_kuali_increments_from_its_base(self):
        self.assertEqual(self._create_employee(self.kuali).employee_number, '300700')
        self.assertEqual(self._create_employee(self.kuali).employee_number, '300701')
        self.assertEqual(self.env['hr.employee']._get_next_employee_number(self.kuali.id), '300702')

    def test_kuali_ignores_low_legacy_numbers(self):
        self._create_employee(self.kuali, employee_number='00012')
        self._create_employee(self.kuali, employee_number='K00003')
        self.assertEqual(self.env['hr.employee']._get_next_employee_number(self.kuali.id), '300700')

    def test_kuali_detected_by_name_or_patron(self):
        Company = self.env['res.company']
        self.assertTrue(Company.create({'name': 'KUALI'})._is_kuali())
        self.assertTrue(Company.create({'name': 'Otra', 'patron': 'corporativo_comunicacion'})._is_kuali())
        self.assertFalse(self.estevez._is_kuali())

    def test_estevez_keeps_original_sequence(self):
        self.assertEqual(self.env['hr.employee']._get_next_employee_number(self.estevez.id), '00001')
        self._create_employee(self.estevez, employee_number='00041')
        self.assertEqual(self.env['hr.employee']._get_next_employee_number(self.estevez.id), '00042')

    def test_company_series_field_overrides_default(self):
        self.estevez.employee_number_start = 500000
        self.assertEqual(self.env['hr.employee']._get_next_employee_number(self.estevez.id), '500001')

    def test_numbers_are_digits_only(self):
        for company in (self.kuali, self.estevez):
            self.assertTrue(self.env['hr.employee']._get_next_employee_number(company.id).isdigit())
