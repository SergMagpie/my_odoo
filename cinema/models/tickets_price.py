# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields, api


class TicketsPrice(models.Model):
    _name = 'cinema.tickets_price'
    _description = 'cinema.tickets_price'
    currency_id = fields.Many2one(
        'res.currency', string='Currency')

    cinema_movie_show_id = fields.Many2one('cinema.movie_show',
                                           string='Cinema movie show',
                                           required=True)
    place_category_id = fields.Many2one('cinema.place_category',
                                        string='Place category',
                                        required=True)
    price = fields.Monetary('Tickets price')
