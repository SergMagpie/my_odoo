# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MovieShow(models.Model):
    _name = 'cinema.movie_show'
    _description = 'cinema.movie_show'

    number = fields.Integer(required=True)
    cinema_hall_id = fields.Many2one('cinema.hall', string='Cinema hall', required=True)
    date_start = fields.Datetime(required=True)
    date_stop = fields.Datetime(required=True)
    movie_id = fields.Many2one('cinema.movie', string='Movie', required=True)

    genre_id = fields.Char(
        'Genre',
        related='movie_id.genre_id.name',
        readonly=True,
        store=True
    )
    rating = fields.Selection(
        'Rating',
        related='movie_id.rating',
        readonly=True,
        store=True
    )

    remaining_seats = fields.Integer(
        string='Remaining seats',
        compute='_compute_remaining_seats',
        store=False,
    )

    place_category_ids = fields.One2many(
        related='cinema_hall_id.amount_place_category_ids',
        readonly=True,
        store=False,
    )

    def _compute_remaining_seats(self):
        for show in self:
            total_seats = show.cinema_hall_id.number_of_seats
            occupied_places = self.env['cinema.ticket'].search_count([('cinema_movie_show_id', '=', show.id)])
            show.remaining_seats = total_seats - occupied_places

    def name_get(self):
        result = []
        for record in self:
            rec_name = "%s > %s (%s) > %s" % (record.cinema_hall_id.cinema_id.name,
                                              record.cinema_hall_id.name,
                                              record.date_start,
                                              record.movie_id.name)
            result.append((record.id, rec_name))
        return result
