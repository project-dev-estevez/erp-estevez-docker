# -*- coding: utf-8 -*-

from odoo import models, api, _
import werkzeug
from odoo.exceptions import UserError

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    def action_print_survey(self, answer=None):
        """Sobreescribe el método para forzar la visualización de resultados."""
        self.ensure_one()
        
        if answer:
            # Forzar modo "preview" que ignora el estado de la encuesta
            url_params = {
                'answer_token': answer.access_token,
                'show_results': '1',
                'preview': '1'  # Este parámetro es clave para evitar el mensaje de encuesta cerrada
            }
        else:
            url_params = {'answer_token': None}

        return {
            'type': 'ir.actions.act_url',
            'name': _("Print Survey"),
            'target': 'new',
            'url': '%s?%s' % (self.get_print_url(), werkzeug.urls.url_encode(url_params)),
        }