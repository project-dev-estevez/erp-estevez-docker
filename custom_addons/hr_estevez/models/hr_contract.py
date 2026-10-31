import re

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta 
import logging

_logger = logging.getLogger(__name__)

# Nombres automáticos: "Contrato Inicial" (el primero), "Contrato N" (renovaciones) y
# "Contrato Final" (tipo de contrato indeterminado). Un nombre escrito a mano no se toca.
INITIAL_CONTRACT_NAME = 'Contrato Inicial'
FINAL_CONTRACT_NAME = 'Contrato Final'
_AUTO_CONTRACT_NAME_RE = re.compile(r'^Contrato (Inicial|Final|\d+)$')

class HrContract(models.Model):
    
    _inherit = 'hr.contract'

    date_of_entry = fields.Date(string='Fecha de Ingreso')
    days_to_expiry = fields.Integer(string='Días para Vencimiento', compute='_compute_days_to_expiry')
    bank = fields.Char(string='Banco')
    bank_account = fields.Char(string='Cuenta Bancaria')
    clabe = fields.Char(string='CLABE')
    work_location = fields.Char(
        string='Ubicación de Trabajo', 
        compute='_compute_employee_contract', 
        store=True
    )
    work_direction = fields.Char(
        string='Dirección', 
        compute='_compute_employee_contract', 
        store=True
    )
    work_area = fields.Char(
        string='Área', 
        compute='_compute_employee_contract', 
        store=True
    )
    department_id = fields.Many2one(
        'hr.department', 
        string='Departamento', 
        compute='_compute_employee_contract', 
        store=True
    )
    job_id = fields.Many2one(
        'hr.job', 
        string='Puesto de Trabajo', 
        compute='_compute_employee_contract', 
        store=True
    )

    contract_duration = fields.Selection([        
        ('30_days', '30 Días'),
        ('60_days', '60 Días'),
        ('90_days', '90 Días'),
        ('180_days', '180 Días'),
        ('1_year', '1 Año'),
        ('2_years', '2 Años'),
        ('indefinite', 'Indefinido'),
        ('custom', 'Personalizado')
    ],  string='Duración del Contrato', default='')

    document_file = fields.Binary(string="Archivo Adjunto", help="Adjunta un único documento relacionado con el contrato.")
    document_filename = fields.Char(string="Nombre del Archivo", compute="_compute_document_filename", store=True)

    payroll_type = fields.Selection(
        related='employee_id.payroll_type',
        readonly=True,
        store=True
    )
 

    @api.onchange('contract_duration', 'date_start')
    def _onchange_contract_duration(self):
        """Calcula automáticamente la fecha fin basado en la duración seleccionada"""
        for contract in self:
            # Solo calcular si se seleccionó una opción válida (no el placeholder)
            if contract.contract_duration and contract.contract_duration != 'custom' and contract.date_start:
                start_date = contract.date_start
                
                # Mapeo de duraciones
                duration_map = {
                    '30_days': relativedelta(days=30),
                    '60_days': relativedelta(days=60),
                    '90_days': relativedelta(days=90),
                    '180_days': relativedelta(days=180),
                    '1_year': relativedelta(years=1),
                    '2_years': relativedelta(years=2),
                }
                
                if contract.contract_duration == 'indefinite':
                    contract.date_end = False
                elif contract.contract_duration in duration_map:
                    contract.date_end = start_date + duration_map[contract.contract_duration]
    
    @api.onchange('date_end')
    def _onchange_date_end(self):
        """Si se modifica manualmente la fecha fin, cambiar a 'Personalizado' solo si es necesario"""
        for contract in self:
            if contract.date_end and contract.date_start:
                # Verificar si la fecha_end actual coincide con la duración seleccionada
                current_duration = contract.contract_duration
                if current_duration and current_duration != 'custom' and current_duration != 'indefinite':
                    # Calcular cuál debería ser la fecha_end para la duración actual
                    duration_map = {
                        '30_days': relativedelta(days=30),
                        '60_days': relativedelta(days=60),
                        '90_days': relativedelta(days=90),
                        '180_days': relativedelta(days=180),
                        '1_year': relativedelta(years=1),
                        '2_years': relativedelta(years=2),
                    }
                    
                    if current_duration in duration_map:
                        expected_end = contract.date_start + duration_map[current_duration]
                        # Si la fecha_end actual NO coincide con la esperada, entonces es personalizado
                        if contract.date_end != expected_end:
                            contract.contract_duration = 'custom'
                else:
                    # Si ya era custom o indefinido, mantenerlo así
                    contract.contract_duration = 'custom'

    def _get_initial_state(self, vals):
        """
        Determina el estado inicial del contrato según la fecha de fin.
        Si la fecha de fin ya venció, retorna 'close', si no, 'open'.
        """
        date_end = vals.get('date_end')
        if date_end:
            today = date.today()
            # Convertir a date si viene como string
            if isinstance(date_end, str):
                try:
                    date_end = datetime.strptime(date_end, "%Y-%m-%d").date()
                except Exception:
                    return 'open'  # Si no se puede convertir, dejar como abierto
            if date_end <= today:
                return 'close'
        return 'open'

    def _compute_document_filename(self):
        for record in self:
            # Generar el nombre del archivo dinámicamente
            record.document_filename = f"Contrato {record.id or 'nuevo'}.pdf"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee_id = vals.get('employee_id')
            if employee_id:
                self._check_can_create_contract(employee_id)
                contract_type = self.env['hr.contract.type'].browse(vals.get('contract_type_id'))
                vals['name'] = self._get_auto_contract_name(employee_id, contract_type)
                employee = self.env['hr.employee'].browse(employee_id)
                vals['work_location'] = employee.work_location_id.name if employee.work_location_id else ''
                vals['work_direction'] = employee.direction_id.name if employee.direction_id else ''
                vals['work_area'] = employee.area_id.name if employee.area_id else ''
                vals['department_id'] = employee.department_id.id if employee.department_id else False
                vals['job_id'] = employee.job_id.id if employee.job_id else False

            if vals.get('contract_duration') == 'indefinite':
                vals['date_end'] = False

            # Determinar el estado inicial usando función separada
            vals['state'] = self._get_initial_state(vals)

        return super(HrContract, self).create(vals_list)

    def write(self, vals):
        # Un contrato indefinido no lleva fecha fin (también al importar o vía API)
        if vals.get('contract_duration') == 'indefinite':
            vals['date_end'] = False
        res = super().write(vals)
        # Al cambiar el tipo de contrato se actualiza el nombre automático (p. ej. a "Contrato Final")
        if 'contract_type_id' in vals and 'name' not in vals:
            for contract in self.filtered(lambda c: c.employee_id and c._has_auto_name()):
                name = contract._get_auto_contract_name(
                    contract.employee_id.id, contract.contract_type_id, before_id=contract.id)
                if contract.name != name:
                    super(HrContract, contract).write({'name': name})
        return res

    @api.model
    def _is_indefinite_contract_type(self, contract_type):
        """Tipo de contrato "Indeterminado" (en cualquier idioma en que se haya capturado)."""
        if not contract_type:
            return False
        names = {contract_type.name, contract_type.with_context(lang='en_US').name}
        return any('indetermin' in (name or '').lower() for name in names)

    @api.model
    def _get_auto_contract_name(self, employee_id, contract_type, before_id=None):
        """Inicial para el primer contrato del empleado, Final si es indeterminado y
        "Contrato N" para los demás. ``before_id``: id del contrato ya guardado, para contar
        solo los anteriores a él."""
        if self._is_indefinite_contract_type(contract_type):
            return FINAL_CONTRACT_NAME
        domain = [('employee_id', '=', employee_id)]
        if before_id:
            domain.append(('id', '<', before_id))
        previous = self.with_context(active_test=False).search_count(domain)
        return INITIAL_CONTRACT_NAME if not previous else f"Contrato {previous + 1}"

    def _has_auto_name(self):
        self.ensure_one()
        return not self.name or bool(_AUTO_CONTRACT_NAME_RE.match(self.name))

    @api.model
    def _get_blocking_contract(self, employee_id):
        """Contrato que impide crear uno nuevo: uno en borrador o en proceso, o el más
        reciente si está vencido. Solo se puede crear un contrato nuevo cuando el actual
        está cancelado."""
        contracts = self.with_context(active_test=False).search(
            [('employee_id', '=', employee_id)], order='date_start desc, id desc')
        pending = contracts.filtered(lambda c: c.state in ('draft', 'open'))
        if pending:
            return pending[0]
        if contracts[:1].state == 'close':
            return contracts[:1]
        return self.browse()

    @api.model
    def _check_can_create_contract(self, employee_id):
        if self.env.context.get('skip_contract_creation_check'):
            return
        blocking = self._get_blocking_contract(employee_id)
        if blocking:
            state = {'draft': 'en borrador', 'open': 'en proceso', 'close': 'vencido'}[blocking.state]
            raise UserError(_(
                "No se puede crear un contrato nuevo para %(employee)s: su contrato actual "
                "«%(contract)s» está %(state)s.\n\nCancela ese contrato primero y después crea el nuevo.",
                employee=blocking.employee_id.name, contract=blocking.name, state=state,
            ))

    @api.onchange('contract_type_id')
    def _onchange_contract_type_name(self):
        for contract in self:
            if contract.employee_id and contract._has_auto_name():
                contract.name = self._get_auto_contract_name(
                    contract.employee_id.id, contract.contract_type_id, before_id=contract._origin.id)
    
    @api.onchange('employee_id')
    def _onchange_employee_id_copy_bank_data(self):
        if self.employee_id:
            last_contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('id', '!=', self.id),
                ('state', 'in', ['draft', 'open', 'close'])
            ], order='date_start desc', limit=1)
            if last_contract:
                self.bank = last_contract.bank
                self.bank_account = last_contract.bank_account
                self.clabe = last_contract.clabe

    @api.depends('date_start', 'date_end')
    def _compute_days_to_expiry(self):
        for contract in self:
            if contract.date_end:
                today = date.today()
                contract.days_to_expiry = (contract.date_end - today).days
            else:
                contract.days_to_expiry = 0

    @api.depends('employee_id', 
             'employee_id.work_location_id', 
             'employee_id.direction_id', 
             'employee_id.area_id', 
             'employee_id.department_id', 
             'employee_id.job_id')
    def _compute_employee_contract(self):
        for contract in self:
            if contract.employee_id:
                contract.work_location = contract.employee_id.work_location_id.name if contract.employee_id.work_location_id else ''
                contract.work_direction = contract.employee_id.direction_id.name if contract.employee_id.direction_id else ''
                contract.work_area = contract.employee_id.area_id.name if contract.employee_id.area_id else ''
                contract.department_id = contract.employee_id.department_id if contract.employee_id.department_id else False
                contract.job_id = contract.employee_id.job_id if contract.employee_id.job_id else False
            else:
                contract.work_location = ''
                contract.work_direction = ''
                contract.work_area = ''
                contract.department_id = False
                contract.job_id = False

    @api.model
    def default_get(self, fields_list):
        res = super(HrContract, self).default_get(fields_list)
        # Si hay empleado, buscar el último contrato y copiar datos bancarios
        employee_id = res.get('employee_id')
        if employee_id:
            # Buscar el último contrato (por fecha de inicio más reciente)
            last_contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee_id),
                ('state', 'in', ['draft', 'open', 'close'])
            ], order='date_start desc', limit=1)
            if last_contract:
                res['bank'] = last_contract.bank
                res['bank_account'] = last_contract.bank_account
                res['clabe'] = last_contract.clabe
            # Avisar antes de llenar el formulario si el contrato actual no está cancelado
            self._check_can_create_contract(employee_id)
            res['name'] = self._get_auto_contract_name(employee_id, self.env['hr.contract.type'])
            employee = self.env['hr.employee'].browse(employee_id)
            res['work_location'] = employee.work_location_id.name if employee.work_location_id else ''
            res['work_direction'] = employee.direction_id.name if employee.direction_id else ''
            res['work_area'] = employee.area_id.name if employee.area_id else ''
            res['department_id'] = employee.department_id.id if employee.department_id else False
            res['job_id'] = employee.job_id.id if employee.job_id else False
            res['date_of_entry'] = employee.employment_start_date or False
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id_copy_bank_data(self):
        if self.employee_id:
            last_contract = self.env['hr.contract'].search([
                ('employee_id', '=', self.employee_id.id),
                ('id', '!=', self.id),
                ('state', 'in', ['draft', 'open', 'close'])
            ], order='date_start desc', limit=1)
            if last_contract:
                self.bank = last_contract.bank
                self.bank_account = last_contract.bank_account
                self.clabe = last_contract.clabe
            # Asignar nombre automático (Inicial / Contrato N / Final)
            self.name = self._get_auto_contract_name(
                self.employee_id.id, self.contract_type_id, before_id=self._origin.id)
    
    def action_save(self):
        """Manually save the record."""
        self.ensure_one()
        self.write(self._convert_to_write(self._cache))

    def action_cancel_contract(self):
        for contract in self:
            contract.state = 'cancel'

    def get_current_month_in_spanish(self):
        """Returns the current month in Spanish."""
        months = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
            'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
            'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        current_month = datetime.now().strftime('%B')
        return months.get(current_month, current_month)

    def get_formatted_date_start_full(self):
        """Return date_start formatted as 'DD DE MES YYYY' in uppercase Spanish."""
        self.ensure_one()
        if not self.date_start:
            return ''

        months = {
            1: 'ENERO',
            2: 'FEBRERO',
            3: 'MARZO',
            4: 'ABRIL',
            5: 'MAYO',
            6: 'JUNIO',
            7: 'JULIO',
            8: 'AGOSTO',
            9: 'SEPTIEMBRE',
            10: 'OCTUBRE',
            11: 'NOVIEMBRE',
            12: 'DICIEMBRE',
        }

        return f"{self.date_start.day:02d} DE {months.get(self.date_start.month, '')} {self.date_start.year}"
    
    def notify_expired_contracts(self):
        """Notifica a los empleados del área de gestión de talento sobre contratos vencidos."""
        today = date.today()
        expired_contracts = self.search([('date_end', '<', today), ('state', '=', 'close')])

        if not expired_contracts:
            return

        # Obtener empleados del área de Gestión de Talento
        employee_management_area = self.env['hr.area'].search([('name', 'ilike', 'Gestión de Talento')], limit=1)

        if not employee_management_area:
            _logger.info("No se encontró el área de Gestión de Talento.")
            return

        employees = self.env['hr.employee'].search([('area_id', '=', employee_management_area.id)])        
        partners = employees.mapped('user_id.partner_id')

        # Enviar notificación
        try:
            # Crear un mensaje en un contrato específico o usar un contrato ficticio
            notification_contract = expired_contracts[0]  # Usamos el primer contrato vencido como "anfitrión"
            notification_contract.message_post(
                subject=_("Contratos Vencidos"),
                body=_("¡Atención! Se han detectado %d contratos vencidos. Por favor, revisa la lista de contratos.") % len(expired_contracts),
                partner_ids=partners.ids,
                subtype_xmlid='mail.mt_comment',
                message_type='notification',
            )
            _logger.info("Notificación amigable enviada sobre contratos vencidos.")
        except Exception as e:
            _logger.error("Error al enviar la notificación: %s", str(e))

        # TODO: Enviar correo
        