from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date
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