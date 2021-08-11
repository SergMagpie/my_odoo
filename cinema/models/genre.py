# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Movie(models.Model):
    _name = 'cinema.genre'
    _description = 'cinema.genre'

    name = fields.Char(required=True, default="Any genre")


