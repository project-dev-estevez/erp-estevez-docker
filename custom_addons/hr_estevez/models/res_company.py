import unicodedata

from odoo import models, fields

# Primer número de empleado de Kuali (Corporativo en Comunicación Digital del Futuro).
# Rango separado del de Estevez porque CodeIgniter guarda el número como INT(11).
KUALI_FIRST_EMPLOYEE_NUMBER = 300700
KUALI_NAME_MARKERS = ('KUALI', 'DIGITAL DEL FUTURO')


class ResCompany(models.Model):
    _inherit = 'res.company'

    patron = fields.Selection([
        # Asegúrate de que las mayúsculas, comas y puntos sean idénticos a los de CodeIgniter
        ('estevezjor', 'ESTEVEZ.JOR SERVICIOS, S.A. DE C.V.'),
        ('corporativo_comunicacion', 'CORPORATIVO EN COMUNICACION DIGITAL DEL FUTURO, S.A. DE C.V.'),
        ('planta_ambientalista', 'PLANTA AMBIENTALISTA EESZ S.A. DE C.V.'),
        ('herrajes', 'HERRAJES ESTEVEZ, S.A. DE C.V.'),
        ('rastreo', 'RASTREO SATELITAL DE MEXICO J&J S.A. DE C.V.'),
        ('grupo_back', 'GRUPO BACK BONE DE MEXICO S.A. DE C.V.')
    ], string='Patrón Fiscal')

    employee_number_start = fields.Integer(
        string='Serie de Número de Empleado',
        default=0,
        help='Base numérica de los números de empleado de esta empresa: el primero será base + 1. '
             'Si se deja en 0, Kuali usa 300699 (primer número 300700) y las demás empresas 0. '
             'Los números deben ser solo dígitos porque CodeIgniter los guarda como INT(11).')

    def _is_kuali(self):
        """Kuali se identifica por su patrón fiscal o por su nombre (sin acentos ni mayúsculas)."""
        self.ensure_one()
        if self.patron == 'corporativo_comunicacion':
            return True
        name = unicodedata.normalize('NFKD', self.name or '').encode('ascii', 'ignore').decode().upper()
        return any(marker in name for marker in KUALI_NAME_MARKERS)

    def _get_employee_number_base(self):
        """Número a partir del cual se cuentan los empleados de la empresa (el siguiente es base + 1)."""
        self.ensure_one()
        if self.employee_number_start:
            return self.employee_number_start
        if self._is_kuali():
            return KUALI_FIRST_EMPLOYEE_NUMBER - 1
        return 0
