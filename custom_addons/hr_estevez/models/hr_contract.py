from odoo import api, models, fields, exceptions, _
from datetime import date, datetime

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

    def _compute_document_filename(self):
        for record in self:
            # Generar el nombre del archivo dinámicamente
            record.document_filename = f"Contrato {record.id or 'nuevo'}.pdf"

    def create(self, vals):
        # Obtener el empleado del contrato que se está creando
        employee_id = vals.get('employee_id')
        if employee_id:
            # Buscar contratos existentes del empleado en los estados 'draft', 'open', o 'close'
            existing_contracts = self.env['hr.contract'].search([
                ('employee_id', '=', employee_id),
                ('state', 'in', ['draft', 'open', 'close'])
            ])
            if existing_contracts:
                raise exceptions.ValidationError(_(
                    "No se puede crear un nuevo contrato porque el empleado ya tiene un contrato registrado."
                ))

            # Establecer valores relacionados con el empleado
            employee = self.env['hr.employee'].browse(employee_id)
            vals['work_location'] = employee.work_location_id.name if employee.work_location_id else ''
            vals['work_direction'] = employee.direction_id.name if employee.direction_id else ''
            vals['work_area'] = employee.area_id.name if employee.area_id else ''
            vals['department_id'] = employee.department_id.id if employee.department_id else False
            vals['job_id'] = employee.job_id.id if employee.job_id else False

        # Establecer el estado inicial como 'open'
        vals['state'] = 'open'

        # Si no hay conflictos, proceder con la creación del contrato
        return super(HrContract, self).create(vals)

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
        
        # Validar si el empleado ya tiene un contrato conflictivo
        if 'employee_id' in res and res['employee_id']:
            existing_contracts = self.env['hr.contract'].search([
                ('employee_id', '=', res['employee_id']),
                ('state', 'in', ['draft', 'open', 'close'])
            ])
            if existing_contracts:
                raise exceptions.ValidationError(_(
                    "El empleado ya tiene un contrato en curso. No se puede crear un nuevo contrato hasta no cerrar el actual."
                ))
        
        # Lógica existente para cargar valores predeterminados
        if 'employee_id' in res:
            employee = self.env['hr.employee'].browse(res['employee_id'])
            res['work_location'] = employee.work_location_id.name if employee.work_location_id else ''
            res['work_direction'] = employee.direction_id.name if employee.direction_id else ''
            res['work_area'] = employee.area_id.name if employee.area_id else ''
            res['department_id'] = employee.department_id.id if employee.department_id else False
            res['job_id'] = employee.job_id.id if employee.job_id else False
        
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