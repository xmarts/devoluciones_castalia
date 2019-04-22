# -*- coding: utf-8 -*-
from odoo import http

# class Devoluciones(http.Controller):
#     @http.route('/devoluciones/devoluciones/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/devoluciones/devoluciones/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('devoluciones.listing', {
#             'root': '/devoluciones/devoluciones',
#             'objects': http.request.env['devoluciones.devoluciones'].search([]),
#         })

#     @http.route('/devoluciones/devoluciones/objects/<model("devoluciones.devoluciones"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('devoluciones.object', {
#             'object': obj
#         })