from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    patron = fields.Selection([
        # Asegúrate de que las mayúsculas, comas y puntos sean idénticos a los de CodeIgniter
        ('estevezjor', 'ESTEVEZ.JOR SERVICIOS, S.A. DE C.V.'), 
        ('corporativo_comunicacion', 'CORPORATIVO EN COMUNICACION DIGITAL DEL FUTURO, S.A. DE C.V.'),
        ('planta_ambientalista', 'PLANTA AMBIENTALISTA EESZ S.A. DE C.V.'),
        ('herrajes', 'HERRAJES ESTEVEZ, S.A. DE C.V.'),
        ('rastreo', 'RASTREO SATELITAL DE MEXICO J&J S.A. DE C.V.'),
        ('grupo_back', 'GRUPO BACK BONE DE MEXICO S.A. DE C.V.')
    ], string='Patrón Fiscal')