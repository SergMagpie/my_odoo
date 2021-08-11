# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CinemaHall(models.Model):
    _name = 'cinema.hall'
    _description = 'cinema.hall'

    name = fields.Char(required=True, default="Any cinema hall")
    number_of_seats = fields.Integer(required=True)
    cinema_id = fields.Many2one('cinema.cinema', required=True, string='Cinema')

    def name_get(self):
        result = []
        for record in self:
            rec_name = "%s (%s)" % (record.cinema_id.name, record.name)
            result.append((record.id, rec_name))
        return result
