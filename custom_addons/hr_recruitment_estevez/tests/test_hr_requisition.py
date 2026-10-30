# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, new_test_user


class TestHrRequisition(TransactionCase):
    """Flujo de la requisición: Borrador → Aprobación Dirección → Aprobación final → Aprobada"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        groups = 'base.group_user'
        cls.user_requestor = new_test_user(cls.env, login='req_solicitante', groups=groups)
        cls.user_director = new_test_user(cls.env, login='req_director', groups=groups)
        cls.user_boss = new_test_user(cls.env, login='req_jefe', groups=groups)
        cls.user_other = new_test_user(cls.env, login='req_otro', groups=groups)
        cls.user_hr = new_test_user(
            cls.env, login='req_th', groups='base.group_user,hr_recruitment.group_hr_recruitment_manager')

        Employee = cls.env['hr.employee']
        cls.boss = Employee.create({'name': 'Jefe Req', 'user_id': cls.user_boss.id, 'marital': 'single'})
        cls.director = Employee.create({
            'name': 'Director Req', 'user_id': cls.user_director.id, 'parent_id': cls.boss.id, 'marital': 'single'})
        cls.direction = cls.env['hr.direction'].create({'name': 'Dirección Req', 'director_id': cls.director.id})
        cls.director.direction_id = cls.direction
        Employee.create({
            'name': 'Solicitante Req', 'user_id': cls.user_requestor.id, 'direction_id': cls.direction.id,
            'parent_id': cls.director.id, 'marital': 'single'})

        cls.department = cls.env['hr.department'].create({'name': 'Área Req', 'direction_id': cls.direction.id})
        cls.job = cls.env['hr.job'].create({'name': 'Puesto Req', 'department_id': cls.department.id})

    def _complete_requisition(self, user=None):
        return self.env['hr.requisition'].with_user(user or self.user_requestor).create({
            'requisition_type': 'new_creation',
            'job_type': 'administrative',
            'workstation_direction_id': self.direction.id,
            'workstation_department_id': self.department.id,
            'workstation_job_id': self.job.id,
            'number_of_vacancies': 2,
        })

    def test_new_requisition_is_draft_without_folio(self):
        requisition = self._complete_requisition()
        self.assertEqual(requisition.state, 'draft')
        self.assertFalse(requisition.folio)
        self.assertEqual(requisition.name, 'Requisición · Puesto Req')

    def test_next_step_requires_fields(self):
        requisition = self.env['hr.requisition'].with_user(self.user_requestor).create({})
        with self.assertRaises(ValidationError):
            requisition.action_next()
        requisition.requisition_type = 'new_creation'
        requisition.action_next()
        self.assertEqual(requisition.wizard_step, 'datos_puesto')
        # Paso 2 incompleto: no deja avanzar ni enviar
        with self.assertRaises(ValidationError):
            requisition.action_next()
        with self.assertRaises(ValidationError):
            requisition.action_submit()

    def test_go_to_step_cannot_skip_incomplete_steps(self):
        requisition = self.env['hr.requisition'].with_user(self.user_requestor).create({})
        with self.assertRaises(ValidationError):
            requisition.with_context(wizard_step='equipo').action_go_to_step()
        requisition.write({'requisition_type': 'new_creation', 'wizard_step': 'datos_puesto'})
        requisition.with_context(wizard_step='especificaciones').action_go_to_step()
        self.assertEqual(requisition.wizard_step, 'especificaciones')

    def test_full_approval_flow(self):
        requisition = self._complete_requisition()
        requisition.action_submit()
        self.assertEqual(requisition.state, 'to_approve')
        self.assertTrue(requisition.folio.startswith('REQ-'))
        self.assertIn(requisition.folio, requisition.name)
        self.assertEqual(requisition.pending_approver_id, self.user_director)

        # Nadie más que el Director puede dar la 1ª aprobación
        for user in (self.user_requestor, self.user_other, self.user_boss, self.user_hr):
            self.assertFalse(requisition.with_user(user).is_current_approver)
            with self.assertRaises(UserError):
                requisition.with_user(user).action_approve()

        requisition.with_user(self.user_director).action_approve()
        self.assertEqual(requisition.state, 'first_approval')
        self.assertEqual(requisition.first_approver_id, self.user_director)
        self.assertEqual(requisition.pending_approver_id, self.user_boss)

        with self.assertRaises(UserError):
            requisition.with_user(self.user_director).action_confirm_approve()
        requisition.with_user(self.user_boss).action_confirm_approve()
        self.assertEqual(requisition.state, 'approved')
        self.assertEqual(requisition.final_approver_id, self.user_boss)
        self.assertEqual(requisition.publication_status, 'Cerrada')

    def test_director_as_requestor_skips_first_approval(self):
        requisition = self._complete_requisition(self.user_director)
        requisition.action_submit()
        self.assertEqual(requisition.state, 'first_approval')
        self.assertEqual(requisition.first_approver_id, self.user_director)
        self.assertEqual(requisition.pending_approver_id, self.user_boss)

    def test_without_director_hr_can_approve(self):
        self.direction.director_id = False
        requisition = self._complete_requisition()
        requisition.action_submit()
        self.assertFalse(requisition.pending_approver_id)
        self.assertFalse(requisition.with_user(self.user_other).is_current_approver)
        self.assertTrue(requisition.with_user(self.user_hr).is_current_approver)
        requisition.with_user(self.user_hr).action_approve()
        self.assertEqual(requisition.state, 'first_approval')

    def test_reject_with_reason_and_resubmit(self):
        requisition = self._complete_requisition()
        requisition.action_submit()
        folio = requisition.folio

        wizard_action = requisition.with_user(self.user_director).action_reject()
        self.assertEqual(wizard_action['res_model'], 'hr.requisition.reject.wizard')
        wizard = self.env['hr.requisition.reject.wizard'].with_user(self.user_director).create({
            'requisition_id': requisition.id, 'reason': 'Falta presupuesto'})
        wizard.action_confirm()
        self.assertEqual(requisition.state, 'rejected')
        self.assertEqual(requisition.rejection_reason, 'Falta presupuesto')
        self.assertEqual(requisition.rejected_by_id, self.user_director)
        self.assertEqual(requisition.publication_status, 'No aplica')

        # Otro usuario no puede regresarla a borrador; el solicitante sí
        with self.assertRaises(UserError):
            requisition.with_user(self.user_other).action_reset_to_draft()
        requisition.with_user(self.user_requestor).action_reset_to_draft()
        self.assertEqual(requisition.state, 'draft')

        # Al reenviar conserva su folio y se limpia el rechazo
        requisition.action_submit()
        self.assertEqual(requisition.folio, folio)
        self.assertFalse(requisition.rejection_reason)

    def test_reset_approved_only_hr_and_closes_vacancy(self):
        requisition = self._complete_requisition()
        requisition.action_submit()
        requisition.with_user(self.user_director).action_approve()
        requisition.with_user(self.user_boss).action_confirm_approve()
        requisition.action_publish_vacancy()
        self.assertTrue(self.job.is_published)

        with self.assertRaises(UserError):
            requisition.with_user(self.user_requestor).action_reset_to_draft()
        requisition.with_user(self.user_hr).action_reset_to_draft()
        self.assertEqual(requisition.state, 'draft')
        self.assertFalse(requisition.is_published)
        self.assertFalse(self.job.is_published)
