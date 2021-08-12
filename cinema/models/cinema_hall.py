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

    def calculate_seats(self, hall_id):
        # counts the number of seats by category
        rez = {}
        hall = self.env['cinema.hall'].search(
            [('id', '=', hall_id)])
        amount_places = self.env['cinema.amount_places'].search(
            [('cinema_hall_id', '=', hall_id)])
        for record in amount_places:
            if record.place_category_id.id in rez:
                rez[record.place_category_id.name] += record.amount
            else:
                rez[record.place_category_id.name] = record.amount
        if sum(rez.values()) < hall.number_of_seats:
            rez['Uncategorized'] = hall.number_of_seats - sum(rez.values())
        a = 2
        return rez
