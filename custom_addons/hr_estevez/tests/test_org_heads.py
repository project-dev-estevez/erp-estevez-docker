# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestOrgHeads(TransactionCase):
    """Director, gerente y coordinador se quitan al dar de baja y los ocupa quien recibe su puesto.
    Al dar de baja también se desactiva el usuario del empleado."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, skip_codeigniter_sync=True, tracking_disable=True))
        Job = cls.env['hr.job']
        cls.job_director = Job.create({'name': 'Director de Prueba'})
        cls.job_manager = Job.create({'name': 'Gerente de Prueba'})
        cls.job_coordinator = Job.create({'name': 'Coordinador de Prueba'})
        cls.job_other = Job.create({'name': 'Auxiliar de Prueba'})
        cls.direction = cls.env['hr.direction'].create({
            'name': 'Dirección de Prueba', 'director_job_id': cls.job_director.id})
        cls.department = cls.env['hr.department'].create({
            'name': 'Área de Prueba', 'direction_id': cls.direction.id, 'manager_job_id': cls.job_manager.id})
        cls.area = cls.env['hr.area'].create({
            'name': 'Departamento de Prueba', 'department_id': cls.department.id,
            'direction_id': cls.direction.id, 'coordinator_job_id': cls.job_coordinator.id})
        cls.counter = 0

    def _employee(self, job, **vals):
        self.__class__.counter += 1
        n = self.counter
        return self.env['hr.employee'].create({
            'names': f'Titular {n}', 'last_name': 'Prueba', 'mother_last_name': 'Organigrama',
            'employee_number': f'ORG{n:03d}', 'barcode': f'ORG{n:03d}',
            'job_id': job.id, 'direction_id': self.direction.id,
            'department_id': self.department.id, 'area_id': self.area.id, **vals,
        })

    def _terminate(self, employee):
        self.env['hr.employee.archive.wizard'].create({
            'employee_id': employee.id,
            'termination_type': 'voluntary_resignation',
            'reason': 'Prueba',
        }).confirm_archive()

    def test_new_employee_with_head_job_becomes_head(self):
        director = self._employee(self.job_director)
        manager = self._employee(self.job_manager)
        coordinator = self._employee(self.job_coordinator)
        self.assertEqual(self.direction.director_id, director)
        self.assertEqual(self.department.manager_id, manager)
        self.assertEqual(self.area.coordinator_id, coordinator)

    def test_termination_clears_heads(self):
        manager = self._employee(self.job_manager)
        coordinator = self._employee(self.job_coordinator)
        self._terminate(manager)
        coordinator.action_archive()
        self.assertFalse(self.department.manager_id)
        self.assertFalse(self.area.coordinator_id)

    def test_successor_takes_vacant_head(self):
        manager = self._employee(self.job_manager)
        teammate = self._employee(self.job_other)
        self.assertEqual(teammate.parent_id, manager)
        self._terminate(manager)
        successor = self._employee(self.job_other)
        successor.write({'job_id': self.job_manager.id})
        self.assertEqual(self.department.manager_id, successor)
        # Odoo reasigna el jefe directo de la gente del área al nuevo gerente
        self.assertEqual(teammate.parent_id, successor)

    def test_current_head_is_not_replaced(self):
        manager = self._employee(self.job_manager)
        self._employee(self.job_manager)
        self.assertEqual(self.department.manager_id, manager)

    def test_head_who_changed_job_is_replaced(self):
        manager = self._employee(self.job_manager)
        manager.write({'job_id': self.job_other.id})
        successor = self._employee(self.job_manager)
        self.assertEqual(self.department.manager_id, successor)

    def test_head_job_in_another_department_does_not_take_head(self):
        other_department = self.env['hr.department'].create({'name': 'Otra Área de Prueba'})
        self._employee(self.job_manager, department_id=other_department.id)
        self.assertFalse(self.department.manager_id)

    def test_termination_deactivates_user(self):
        user = self.env['res.users'].create({'name': 'Usuario Baja', 'login': 'usuario.baja.prueba'})
        employee = self._employee(self.job_other, user_id=user.id)
        self._terminate(employee)
        self.assertFalse(user.active)

    def test_termination_keeps_user_with_other_active_employee(self):
        company = self.env['res.company'].create({'name': 'Empresa de Prueba'})
        user = self.env['res.users'].create({
            'name': 'Usuario Doble', 'login': 'usuario.doble.prueba',
            'company_ids': [(6, 0, [self.env.company.id, company.id])]})
        employee = self._employee(self.job_other, user_id=user.id)
        self.env['hr.employee'].create({
            'names': 'Otra', 'last_name': 'Empresa', 'employee_number': 'ORG999', 'barcode': 'ORG999',
            'user_id': user.id, 'company_id': company.id,
            # El horario por defecto es de la empresa principal y Odoo no permite mezclarlos
            'resource_calendar_id': False,
        })
        self._terminate(employee)
        self.assertTrue(user.active)
