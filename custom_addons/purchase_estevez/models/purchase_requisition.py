from odoo import models, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_all_alternatives(self):
        # Obtener todos los purchase_group_id de las solicitudes seleccionadas
        purchase_group_ids = self.mapped('purchase_group_id').ids
        
        # Buscar todas las líneas de producto de las alternativas vinculadas
        order_lines = self.env['purchase.order.line'].search([
            ('order_id.purchase_group_id', 'in', purchase_group_ids)
        ])
        
        # Retornar la vista de comparación
        return {
            'type': 'ir.actions.act_window',
            'name': _('Comparar Alternativas'),
            'res_model': 'purchase.order.line',
            'view_mode': 'list',
            'views': [(self.env.ref('purchase_requisition.purchase_order_line_compare_tree').id, 'list')],
            'domain': [('id', 'in', order_lines.ids)],
            'target': 'current',
        }