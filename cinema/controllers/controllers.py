# -*- coding: utf-8 -*-
# from odoo import http


# class Cinema(http.Controller):
#     @http.route('/cinema/cinema/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cinema/cinema/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cinema.listing', {
#             'root': '/cinema/cinema',
#             'objects': http.request.env['cinema.cinema'].search([]),
#         })

#     @http.route('/cinema/cinema/objects/<model("cinema.cinema"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cinema.object', {
#             'object': obj
#         })
