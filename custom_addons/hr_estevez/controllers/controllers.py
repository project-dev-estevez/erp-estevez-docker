# -*- coding: utf-8 -*-
# from odoo import http


# class HrEstevez(http.Controller):
#     @http.route('/hr_estevez/hr_estevez', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_estevez/hr_estevez/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_estevez.listing', {
#             'root': '/hr_estevez/hr_estevez',
#             'objects': http.request.env['hr_estevez.hr_estevez'].search([]),
#         })

#     @http.route('/hr_estevez/hr_estevez/objects/<model("hr_estevez.hr_estevez"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_estevez.object', {
#             'object': obj
#         })

