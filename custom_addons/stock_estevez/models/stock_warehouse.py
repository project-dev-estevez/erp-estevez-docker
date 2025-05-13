from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
import re


class StockRequisitionLine(models.Model):
    _inherit = 'stock.warehouse'

    type_warehouse = fields.Selection([
        ('general_warehouse', 'Almacén General'),
        ('foreign_warehouse', 'Almacén Foraneo'),
        ('specialized warehouse', 'Almacén Especializado')
    ], string='Tipo Almacén')

    sub_type_warehouse = fields.Selection([
        ('sub_warehouse', 'Sub-almacen'),
        ('project_warehouse', 'Almacén Proyecto'),
        ('contractors_warehouse', 'Almacén Contratista'),
        ('mobile_warehouse', 'Almacén Móvil')
    ], string='Subtipo Almacén')
 
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse", 
        string="Almacén", 
        help="Selecciona un almacén de la lista."
    )        

    project_name = fields.Char(string="Nombre del proyecto")
    location = fields.Char(string="Ubicación")
    responsible_ag = fields.Many2one(
        "hr.employee",
        string="Responsable AG",
        help="Persona responsable almacén"
    )
    responsible_dno = fields.Many2one(
        "hr.employee",
        string="Responsable DNO",
        help="Persona responsable"
    )

    contractors_name = fields.Char(string="Nombre de contratista")
    assignment_sheet = fields.Char(string="Hoja de asignacion")
