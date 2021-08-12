# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Movie(models.Model):
    _name = 'cinema.movie'
    _description = 'cinema.movie'
    _inherit = ['mail.thread']

    name = fields.Char(required=True, default="Any movie")
    genre_id = fields.Many2one('cinema.genre', string='Genre')
    release_date = fields.Date()
    director_id = fields.Many2one('res.partner', string='Director movie')
    actors_ids = fields.Many2many('res.partner', string='Actors')
    rating = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Very High')])
    poster = fields.Image()

    movie_show_ids = fields.One2many(
        'cinema.movie_show',
        'movie_id',
        string='Movie show form',
        # context={'search_default_cinema_movie_id': 'active_id'}
    )
