# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from odoo.addons.survey.controllers.main import Survey

from odoo.tools import format_datetime, format_date, is_html_empty

class SurveyCustom(Survey):
    
    @http.route('/survey/print/<string:survey_token>', type='http', auth='public', website=True, sitemap=False)
    def survey_print(self, survey_token, review=False, answer_token=None, **post):
        '''Modificación para forzar la visualización de resultados'''
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False, check_partner=False)
        
        # Forzar la visualización si hay token de respuesta
        if answer_token and access_data['validity_code'] == 'survey_closed':
            access_data['validity_code'] = True
            
        if access_data['validity_code'] is not True and (
                not access_data['has_survey_access'] or
                access_data['validity_code'] not in ['token_required', 'survey_void', 'answer_deadline']):
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        return request.render('survey.survey_page_print', {
            'is_html_empty': is_html_empty,
            'review': review,
            'survey': survey_sudo,
            'answer': answer_sudo if survey_sudo.scoring_type != 'scoring_without_answers' else answer_sudo.browse(),
            'questions_to_display': answer_sudo._get_print_questions(),
            'scoring_display_correction': survey_sudo.scoring_type in ['scoring_with_answers', 'scoring_with_answers_after_page'] and answer_sudo,
            'format_datetime': lambda dt: format_datetime(request.env, dt, dt_format=False),
            'format_date': lambda date: format_date(request.env, date),
            'graph_data': json.dumps(answer_sudo._prepare_statistics()[answer_sudo])
                              if answer_sudo and survey_sudo.scoring_type in ['scoring_with_answers', 'scoring_with_answers_after_page'] else False,
        })