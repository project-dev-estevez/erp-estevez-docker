# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestHrDirection(TransactionCase):
    """Test cases para el modelo hr.direction"""

    def setUp(self):
        """Preparar datos de prueba antes de cada test"""
        super(TestHrDirection, self).setUp()
        
        # Crear empresa de prueba
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })
        
        # Crear empleados de prueba
        self.employee_director = self.env['hr.employee'].create({
            'name': 'Juan Pérez',
            'company_id': self.company.id,
        })
        
        self.employee_subdirector = self.env['hr.employee'].create({
            'name': 'María García',
            'company_id': self.company.id,
        })
        
        # Crear dirección padre de prueba
        self.direction_parent = self.env['hr.direction'].create({
            'name': 'Dirección General',
            'director_id': self.employee_director.id,
            'company_id': self.company.id,
        })

    def test_01_create_direction_basic(self):
        """Test: Crear una dirección básica con campos mínimos"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección de Tecnología',
        })
        
        self.assertTrue(direction)
        self.assertEqual(direction.name, 'Dirección de Tecnología')
        self.assertFalse(direction.director_id)
        self.assertFalse(direction.parent_id)
        self.assertEqual(direction.total_departments, 0)

    def test_02_create_direction_complete(self):
        """Test: Crear una dirección con todos los campos"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección de Recursos Humanos',
            'director_id': self.employee_director.id,
            'company_id': self.company.id,
            'parent_id': self.direction_parent.id,
        })
        
        self.assertEqual(direction.name, 'Dirección de Recursos Humanos')
        self.assertEqual(direction.director_id, self.employee_director)
        self.assertEqual(direction.company_id, self.company)
        self.assertEqual(direction.parent_id, self.direction_parent)

    def test_03_name_required(self):
        """Test: El campo 'name' es obligatorio"""
        with self.assertRaises(ValidationError):
            self.env['hr.direction'].create({
                'director_id': self.employee_director.id,
            })

    def test_04_parent_child_relationship(self):
        """Test: Relación padre-hijo entre direcciones"""
        # Crear dirección hija
        child_direction = self.env['hr.direction'].create({
            'name': 'Subdirección de IT',
            'parent_id': self.direction_parent.id,
        })
        
        # Verificar relación padre-hijo
        self.assertEqual(child_direction.parent_id, self.direction_parent)
        self.assertIn(child_direction, self.direction_parent.child_ids)
        self.assertEqual(len(self.direction_parent.child_ids), 1)

    def test_05_multiple_children(self):
        """Test: Una dirección puede tener múltiples direcciones hijas"""
        child1 = self.env['hr.direction'].create({
            'name': 'Subdirección 1',
            'parent_id': self.direction_parent.id,
        })
        
        child2 = self.env['hr.direction'].create({
            'name': 'Subdirección 2',
            'parent_id': self.direction_parent.id,
        })
        
        child3 = self.env['hr.direction'].create({
            'name': 'Subdirección 3',
            'parent_id': self.direction_parent.id,
        })
        
        self.assertEqual(len(self.direction_parent.child_ids), 3)
        self.assertIn(child1, self.direction_parent.child_ids)
        self.assertIn(child2, self.direction_parent.child_ids)
        self.assertIn(child3, self.direction_parent.child_ids)

    def test_06_compute_total_departments_zero(self):
        """Test: total_departments debe ser 0 cuando no hay departamentos"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección sin Departamentos',
        })
        
        self.assertEqual(direction.total_departments, 0)

    def test_07_compute_total_departments_with_departments(self):
        """Test: total_departments se calcula correctamente"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección con Departamentos',
            'company_id': self.company.id,
        })
        
        # Crear departamentos asociados
        dept1 = self.env['hr.department'].create({
            'name': 'Departamento 1',
            'direction_id': direction.id,
            'company_id': self.company.id,
        })
        
        dept2 = self.env['hr.department'].create({
            'name': 'Departamento 2',
            'direction_id': direction.id,
            'company_id': self.company.id,
        })
        
        dept3 = self.env['hr.department'].create({
            'name': 'Departamento 3',
            'direction_id': direction.id,
            'company_id': self.company.id,
        })
        
        # Verificar el cálculo
        self.assertEqual(len(direction.department_ids), 3)
        self.assertEqual(direction.total_departments, 3)

    def test_08_update_total_departments_on_add(self):
        """Test: total_departments se actualiza al agregar departamentos"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección Test',
            'company_id': self.company.id,
        })
        
        self.assertEqual(direction.total_departments, 0)
        
        # Agregar un departamento
        self.env['hr.department'].create({
            'name': 'Nuevo Departamento',
            'direction_id': direction.id,
            'company_id': self.company.id,
        })
        
        self.assertEqual(direction.total_departments, 1)

    def test_09_update_total_departments_on_remove(self):
        """Test: total_departments se actualiza al eliminar departamentos"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección Test',
            'company_id': self.company.id,
        })
        
        dept = self.env['hr.department'].create({
            'name': 'Departamento Temporal',
            'direction_id': direction.id,
            'company_id': self.company.id,
        })
        
        self.assertEqual(direction.total_departments, 1)
        
        # Eliminar el departamento
        dept.unlink()
        
        self.assertEqual(direction.total_departments, 0)

    def test_10_change_director(self):
        """Test: Cambiar el director de una dirección"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección Test',
            'director_id': self.employee_director.id,
        })
        
        self.assertEqual(direction.director_id, self.employee_director)
        
        # Cambiar director
        direction.write({
            'director_id': self.employee_subdirector.id,
        })
        
        self.assertEqual(direction.director_id, self.employee_subdirector)

    def test_11_direction_without_director(self):
        """Test: Una dirección puede existir sin director asignado"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección sin Director',
        })
        
        self.assertFalse(direction.director_id)

    def test_12_change_parent_direction(self):
        """Test: Cambiar la dirección padre"""
        new_parent = self.env['hr.direction'].create({
            'name': 'Nueva Dirección Padre',
        })
        
        child = self.env['hr.direction'].create({
            'name': 'Dirección Hija',
            'parent_id': self.direction_parent.id,
        })
        
        self.assertEqual(child.parent_id, self.direction_parent)
        
        # Cambiar el padre
        child.write({
            'parent_id': new_parent.id,
        })
        
        self.assertEqual(child.parent_id, new_parent)
        self.assertNotIn(child, self.direction_parent.child_ids)
        self.assertIn(child, new_parent.child_ids)

    def test_13_company_ondelete_set_null(self):
        """Test: Verificar que la dirección no se elimine al borrar la empresa"""
        direction = self.env['hr.direction'].create({
            'name': 'Dirección con Empresa',
            'company_id': self.company.id,
        })
        
        self.assertEqual(direction.company_id, self.company)
        
        # Eliminar la empresa
        company_id = self.company.id
        self.company.unlink()
        
        # La dirección debe seguir existiendo
        self.assertTrue(direction.exists())
        # El campo company_id debe ser False/None
        self.assertFalse(direction.company_id)

    def test_14_hierarchy_three_levels(self):
        """Test: Jerarquía de tres niveles"""
        # Nivel 1: Dirección General
        level1 = self.direction_parent
        
        # Nivel 2: Dirección de Operaciones
        level2 = self.env['hr.direction'].create({
            'name': 'Dirección de Operaciones',
            'parent_id': level1.id,
        })
        
        # Nivel 3: Subdirección de Logística
        level3 = self.env['hr.direction'].create({
            'name': 'Subdirección de Logística',
            'parent_id': level2.id,
        })
        
        # Verificar jerarquía
        self.assertEqual(level3.parent_id, level2)
        self.assertEqual(level2.parent_id, level1)
        self.assertIn(level2, level1.child_ids)
        self.assertIn(level3, level2.child_ids)
