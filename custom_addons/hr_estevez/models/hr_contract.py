from odoo import api, models, fields, exceptions, _
from datetime import date, datetime
import logging

_logger = logging.getLogger(__name__)

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

    document_file = fields.Binary(string="Archivo Adjunto", help="Adjunta un único documento relacionado con el contrato.")
    document_filename = fields.Char(string="Nombre del Archivo", compute="_compute_document_filename", store=True)

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

    def create(self, vals):
        employee_id = vals.get('employee_id')
        if employee_id:
            existing_contracts = self.env['hr.contract'].search([
                ('employee_id', '=', employee_id),
                ('state', 'in', ['draft', 'open', 'close'])
            ])
            if existing_contracts:
                raise exceptions.ValidationError(_(
                    "No se puede crear un nuevo contrato porque el empleado ya tiene un contrato registrado."
                ))
            employee = self.env['hr.employee'].browse(employee_id)
            vals['work_location'] = employee.work_location_id.name if employee.work_location_id else ''
            vals['work_direction'] = employee.direction_id.name if employee.direction_id else ''
            vals['work_area'] = employee.area_id.name if employee.area_id else ''
            vals['department_id'] = employee.department_id.id if employee.department_id else False
            vals['job_id'] = employee.job_id.id if employee.job_id else False

        # Determinar el estado inicial usando función separada
        vals['state'] = self._get_initial_state(vals)

        return super(HrContract, self).create(vals)
    
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
            employee = self.env['hr.employee'].browse(employee_id)
            res['work_location'] = employee.work_location_id.name if employee.work_location_id else ''
            res['work_direction'] = employee.direction_id.name if employee.direction_id else ''
            res['work_area'] = employee.area_id.name if employee.area_id else ''
            res['department_id'] = employee.department_id.id if employee.department_id else False
            res['job_id'] = employee.job_id.id if employee.job_id else False
            res['date_of_entry'] = employee.employment_start_date or False
        return res
    
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
        