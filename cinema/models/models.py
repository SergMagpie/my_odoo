# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Cinema(models.Model):
    _name = 'cinema.cinema'
    _description = 'cinema.cinema'

    name = fields.Char(required=True, default="Any cinema")
    address = fields.Char()
    director_id = fields.Many2one('res.partner', string='Director')


# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     director_ids = fields.One2many('cinema.cinema', 'director_id', string='Director')
    # authored_book_ids = fields.Many2many(
    #     'library.book',
    #     string='Authored Books',
    #     # relation='library_book_res_partner_rel'  # optional
    # )