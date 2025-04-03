from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, timedelta
import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

      # Método para archivar (dar de baja)
    def action_archive_employee(self):
        for employee in self:
            employee.write({'active': False})

    # Método para reactivar
    def action_reactivate_employee(self):
        for employee in self:
            employee.write({'active': True})

    gender = fields.Selection([
        ('male', 'Masculino'),
        ('female', 'Femenino'),
        ('indistinct', 'Indistinto')  # Cambiar la etiqueta de 'other'
    ], groups="hr.group_hr_user", tracking=True)

    # Primera Columna en la Vista de Empleados
    names = fields.Char(string='Nombres')
    last_name = fields.Char(string='Apellido Paterno')
    mother_last_name = fields.Char(string='Apellido Materno')
    employee_number = fields.Char(string='Número de Empleado')
    project = fields.Char(string='Proyecto')

    # Segunda Columna en la Vista de Empleados 
    company_id = fields.Many2one('res.company', string='Company', compute='_compute_company', store=True, readonly=True)
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    area_id = fields.Many2one('hr.area', string='Área')

    # Información de Trabajo
    imss_registration_date = fields.Date(string='Fecha de Alta en IMSS')
    payment_type = fields.Selection([
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
    ], string='Tipo de Pago')
    payroll_type = fields.Selection([
        ('cash', 'Efectivo'),
        ('mixed', 'Mixto'),
        ('imss', 'IMSS'),
    ], string='Tipo de Nómina')


    rfc = fields.Char(string='RFC')
    curp = fields.Char(string='CURP')
    nss = fields.Char(string='NSS')
    voter_key = fields.Char(string='Clave Elector')
    license_number = fields.Char(string='Número de Licencia')
    infonavit = fields.Boolean(string='Infonavit', default=False)
    private_colonia = fields.Char(string="Colonia")
    fiscal_zip = fields.Char(string="Fiscal ZIP")

    work_phone = fields.Char(string='Work Phone', compute=False)
    coach_id = fields.Many2one('hr.employee', string='Instructor', compute=False, store=False)

    name = fields.Char(string='Nombre Completo', compute='_compute_full_name', store=True, readonly=True)
    age = fields.Integer(string='Edad', compute='_compute_age')

    country_id = fields.Many2one('res.country', string='País', default=lambda self: self.env.ref('base.mx').id)
    country_of_birth = fields.Many2one('res.country', string="Country of Birth", groups="hr.group_hr_user", tracking=True, default=lambda self: self.env.ref('base.mx').id)
    private_country_id = fields.Many2one("res.country", string="Private Country", groups="hr.group_hr_user", default=lambda self: self.env.ref('base.mx').id)
    is_mexico = fields.Boolean(string="Is Mexico", compute="_compute_is_mexico", store=False)

    marital = fields.Selection([
        ('single', 'Soltero(a)'),
        ('married', 'Casado(a)'),
        ('cohabitant', 'En Concubinato'),
        ('widower', 'Viudo(a)'),
        ('divorced', 'Divorciado(a)')
    ], string='Estado Civil', required=True, tracking=True)

    spouse_birthdate = fields.Date(string="Spouse Birthdate", groups="hr.group_hr_user", store=False)

    memorandum_ids = fields.One2many('hr.memorandum', 'employee_id', string='Actas Administrativas')

    years_of_service = fields.Float(
        string="Años de Servicio",
        compute="_compute_years_of_service",
        store=False
    )
    entitled_days = fields.Float(
        string="Con Derecho a",
        compute="_compute_vacation_days",
        store=False
    )
    vacation_days_taken = fields.Float(
        string="Días de Vacaciones Disfrutados",
        compute="_compute_vacation_days_taken",
        store=False
    )
    vacation_days_available = fields.Float(
        string="Días de Vacaciones Disponibles",
        compute="_compute_vacation_days_available",
        store=False
    )

    vacation_period_ids = fields.One2many(
        'hr.vacation.period', 'employee_id', string="Periodos de Vacaciones"
    )

    @api.depends('contract_ids.date_start', 'contract_ids.date_end', 'years_of_service')
    def generate_vacation_periods(self):
        for employee in self:
            # Eliminar periodos existentes
            employee.vacation_period_ids.unlink()

            # Verificar si hay contratos y años de servicio
            if not employee.contract_ids or employee.years_of_service <= 0:
                continue

            # Generar periodos basados en los años de servicio
            start_date = min(employee.contract_ids.mapped('date_start'))  # Fecha de inicio más antigua
            years_of_service = int(employee.years_of_service)

            for year in range(years_of_service):
                # Calcular el inicio y fin del periodo basado en años calendario
                year_start = start_date.replace(year=start_date.year + year)
                year_end = year_start.replace(year=year_start.year + 1) - timedelta(days=1)

                entitled_days = 12 + (year * 2) if year < 5 else 22  # Ejemplo de cálculo
                days_taken = 0  # Inicialmente 0
                self.env['hr.vacation.period'].create({
                    'employee_id': employee.id,
                    'year_start': year_start,
                    'year_end': year_end,
                    'entitled_days': entitled_days,
                    'days_taken': days_taken,
                })

    @api.depends('contract_ids.date_start', 'contract_ids.date_end', 'contract_ids.state')
    def _compute_years_of_service(self):
        for employee in self:
            total_days = 0
            today = date.today()

            # Iterar sobre todos los contratos del empleado
            for contract in employee.contract_ids:
                # Considerar solo contratos en estado 'open' o 'close'
                if contract.date_start:
                    # Si el contrato tiene fecha de fin, usarla; de lo contrario, usar la fecha actual
                    end_date = contract.date_end or today
                    total_days += (end_date - contract.date_start).days

            # Convertir días totales en años decimales
            employee.years_of_service = round(total_days / 365.0, 2)

    @api.depends('years_of_service')
    def _compute_vacation_days(self):
        for employee in self:
            years = int(employee.years_of_service)  # Convertir años de servicio a entero
            entitled_days = 0

            # Calcular días de vacaciones acumulativos según los años laborados
            if years >= 1:
                for i in range(1, years + 1):
                    if i == 1:
                        entitled_days += 12
                    elif i == 2:
                        entitled_days += 14
                    elif i == 3:
                        entitled_days += 16
                    elif i == 4:
                        entitled_days += 18
                    elif i == 5:
                        entitled_days += 20
                    elif 6 <= i <= 10:
                        entitled_days += 22
                    elif 11 <= i <= 15:
                        entitled_days += 24
                    elif 16 <= i <= 20:
                        entitled_days += 26
                    elif 21 <= i <= 25:
                        entitled_days += 28
                    elif 26 <= i <= 30:
                        entitled_days += 30
                    elif 31 <= i <= 50:
                        entitled_days += 32

            # Asignar los días calculados al campo
            employee.entitled_days = entitled_days

    @api.depends('entitled_days')
    def _compute_vacation_days_taken(self):
        for employee in self:
            # Inicializar el campo con 0
            employee.vacation_days_taken = 0

            # Obtener los días de vacaciones aprobados para el empleado
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate')  # Solo considerar vacaciones aprobadas
            ])

            # Sumar los días de vacaciones aprobados
            if leaves:
                employee.vacation_days_taken = sum(leaves.mapped('number_of_days'))

    @api.depends('entitled_days', 'vacation_days_taken')
    def _compute_vacation_days_available(self):
        for employee in self:
            # Calcular los días disponibles
            employee.vacation_days_available = employee.entitled_days - employee.vacation_days_taken

    def action_open_memorandum_form(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Acta Administrativa',
            'res_model': 'hr.memorandum',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }

    @api.depends('country_id')
    def _compute_is_mexico(self):
        for record in self:
            record.is_mexico = record.country_id.code == 'MX'

    @api.depends('names', 'last_name', 'mother_last_name')
    def _compute_full_name(self):
        for record in self:
            record.name = f"{record.names} {record.last_name} {record.mother_last_name}"

    @api.onchange('names', 'last_name', 'mother_last_name')
    def _onchange_full_name(self):
        for record in self:
            names = record.names or ''
            last_name = record.last_name or ''
            mother_last_name = record.mother_last_name or ''
            record.name = f"{names} {last_name} {mother_last_name}".strip()

    @api.model
    def create(self, vals):
        if 'names' in vals or 'last_name' in vals or 'mother_last_name' in vals:
            names = vals.get('names', '').strip()
            vals['name'] = f"{names} {vals.get('last_name', '')} {vals.get('mother_last_name', '')}".strip()
        employee = super(HrEmployee, self).create(vals)
        if 'direction_id' in vals and vals['direction_id']:
            direction = self.env['hr.direction'].browse(vals['direction_id'])
            direction.director_id = employee.id
        return employee

    def write(self, vals):
        if 'names' in vals or 'last_name' in vals or 'mother_last_name' in vals:
            names = vals.get('names', self.names).strip()
            vals['name'] = f"{names} {vals.get('last_name', self.last_name)} {vals.get('mother_last_name', self.mother_last_name)}".strip()
        for record in self:
            if 'direction_id' in vals:
                # Si el empleado ya tiene una dirección, desasocia el director de la dirección anterior
                if record.direction_id:
                    old_direction = self.env['hr.direction'].browse(record.direction_id.id)
                    old_direction.director_id = False

                # Asocia el director a la nueva dirección
                if vals['direction_id']:
                    new_direction = self.env['hr.direction'].browse(vals['direction_id'])
                    new_direction.director_id = record.id

        res = super(HrEmployee, self).write(vals)
        return res
    
    @api.depends('birthday')
    def _compute_age(self):
        for record in self:
            if record.birthday:
                today = date.today()
                record.age = today.year - record.birthday.year - ((today.month, today.day) < (record.birthday.month, record.birthday.day))
            else:
                record.age = 0

    def _format_phone_number(self, phone_number):
        if phone_number and not phone_number.startswith('+52'):
            phone_number = '+52 ' + re.sub(r'(\d{3})(\d{3})(\d{4})', r'\1 \2 \3', phone_number)
        return phone_number

    @api.onchange('work_phone')
    def _onchange_work_phone(self):
        if self.work_phone:
            self.work_phone = self._format_phone_number(self.work_phone)

    @api.onchange('private_phone')
    def _onchange_private_phone(self):
        if self.private_phone:
            self.private_phone = self._format_phone_number(self.private_phone)

    def action_open_whatsapp(self):
        for employee in self:
            phone = employee.work_phone or employee.private_phone
            if phone:
                # Eliminar caracteres no numéricos
                phone = re.sub(r'\D', '', phone)
                # Verificar si el número ya tiene un código de país
                if not phone.startswith('52'):
                    phone = '52' + phone
                message = "Hola"
                url = f"https://wa.me/{phone}?text={message}"
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                }
            else:
                raise UserError("The employee does not have a phone number.")
            

    def action_open_documents(self):
        return {
            'name': _('Documentos del Empleado'),
            'view_type': 'form',
            'view_mode': 'kanban,list,form',
            'res_model': 'ir.attachment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('res_model', '=', 'hr.employee'), ('res_id', '=', self.id)],
            'context': {'default_res_model': 'hr.employee', 'default_res_id': self.id, 'create': True, 'edit': True},
        }