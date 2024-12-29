from odoo import api, models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    names = fields.Char(string='Nombres', required=True)
    last_name = fields.Char(string='Apellido Paterno', required=True)
    mother_last_name = fields.Char(string='Apellido Materno', required=True)
    direction_id = fields.Many2one('hr.direction', string='Dirección')
    area_id = fields.Many2one('hr.area', string='Area')
    payment_type = fields.Selection([
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
    ], string='Tipo de Pago', required=True)

    rfc = fields.Char(string='RFC')
    curp = fields.Char(string='CURP')
    nss = fields.Char(string='NSS')
    voter_key = fields.Char(string='Clave Elector')
    license_number = fields.Char(string='Número de Licencia')
    infonavit = fields.Char(string='Infonavit')
    private_colonia = fields.Char(string="Colonia")
    fiscal_zip = fields.Char(string="Fiscal ZIP")

    work_phone = fields.Char(string='Work Phone', compute=False, store=False)
    coach_id = fields.Many2one('hr.employee', string='Instructor', compute=False, store=False)

    name = fields.Char(string='Nombre Completo', compute='_compute_full_name', store=True, readonly=True)

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