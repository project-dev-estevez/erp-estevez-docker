from odoo import models, fields, api

class SlideChannel(models.Model):
    _inherit = 'slide.channel'
            
    representante_patron = fields.Many2one(
        'res.users',
        string="Representante/patrón",
        domain=[            
            ('employee_id', '!=', False),
            ('employee_id.employee_number', '=', '10049')
        ],
        help="Seleccione el representante del patrón"
    )
    
    representante_trabajadores = fields.Many2one(
        'res.users',
        string="Representante de Trabajadores",
        domain=lambda self: [            
            ('employee_id', '!=', False),
            ('employee_id.employee_number', '=', '10049')
        ],
        help="Persona que representanta a los trabajadores"
    )
    
    tipo_agente = fields.Selection(
        selection=[
            ('interno', 'Interno'),
            ('externo', 'Externo'),
            ('otro', 'Otro')
        ],
        string="Tipo de Agente",
        default='interno'
    )
    
    modalidad = fields.Selection(
        selection=[
            ('presencial', 'Presencial'),
            ('en_linea', 'En línea'),
            ('mixta', 'Mixta')
        ],
        string="Modalidad",
        default='presencial'
    )
    