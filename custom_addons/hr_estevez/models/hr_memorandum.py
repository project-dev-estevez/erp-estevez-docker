from odoo import models, fields

class HrMemorandum(models.Model):
    _name = 'hr.memorandum'
    _description = 'Actas Administrativas'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, ondelete='cascade')
    date = fields.Date(string='Fecha del Acta', required=True)
    description = fields.Text(string='Descripción / Hechos', required=True)
    fraction = fields.Char(string='Fracción')
    article = fields.Char(string='Artículo')
    administrative_type = fields.Char(string='Tipo Acta administrativa') 
    
    

    def action_save_memorandum(self):
        # Este método simplemente guarda el registro
        self.ensure_one()  # Asegura que solo se procese un registro a la vez
        return {'type': 'ir.actions.act_window_close'}
    