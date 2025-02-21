import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class PurchaseAcquisition(models.Model):
    _name = 'purchase.acquisition'
    _description = 'Acquisition'

    #Adquisiciones

    fecha_limite_entrega = fields.Date(string='Fecha límite de entrega', required=True)    
    tipo = fields.Char(string='Tipo', required=True, default='Producto')
    proyecto = fields.Char(string='Proyecto', required=True)
    segmento = fields.Char(string='Segmento', required=True)
    prioridad = fields.Selection(
        selection=[            
            ('urgente', 'Urgente'),
            ('recurrente', 'Stock'),
            ('programado', 'Programado'),
        ],
        string='Prioridad', required=True)                   
    almacen = fields.Char(string='Almacen', required=True)
    sugerencia = fields.Char(string='Sugerencia de proveedor', required=True)
    comentarios = fields.Char(string='Comentarios', required=True)
    nombre_producto = fields.Many2one('product.product', string='Nombre del producto', required=True)
    cantidad = fields.Integer(string='Cantidad', required=True)
    medida = fields.Char(string='Unidad de medida', required=True)
    descripcion = fields.Char(string='Descripcion', required=True)
    especificaciones = fields.Char(string='Especificaciones', required=True)

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for record in self:
            if record.cantidad < 0:
                raise ValidationError("La cantidad debe ser mayor que cero")

    @api.constrains('fecha_limite_entrega')
    def _check_fecha_limite_entrega(self):
        for record in self:
            if record.fecha_limite_entrega and record.fecha_limite_entrega < fields.Date.today():
                raise ValidationError("La fecha límite de entrega debe ser posterior a la fecha actual")

    def save_dat(self):
        #Metodo para el bootn de Guardar
        self.ensure_one()
        return {
            "type": "ir.actions.act_window_close",  # Cierra la ventana de este formulario
        }

    

