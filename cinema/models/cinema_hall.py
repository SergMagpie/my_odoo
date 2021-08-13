# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CinemaHall(models.Model):
    _name = 'cinema.hall'
    _description = 'cinema.hall'

    name = fields.Char(required=True, default="Any cinema hall")
    number_of_seats = fields.Integer(
        compute='_compute_calculate_amount_of_seats',
        store=False,
    )
    cinema_id = fields.Many2one('cinema.cinema', required=True, string='Cinema')

    amount_place_category_ids = fields.One2many(
        'cinema.amount_places',
        'cinema_hall_id',
        string='Place category',

    )

    def name_get(self):
        result = []
        for record in self:
            rec_name = "%s (%s)" % (record.cinema_id.name, record.name)
            result.append((record.id, rec_name))
        return result

    def _compute_calculate_amount_of_seats(self):
        for hall in self:
            rez = 0
            list_of_seats = self.env['cinema.amount_places'].search(
                [('cinema_hall_id', '=', hall.id)])
            for category in list_of_seats:
                rez += category.amount
            hall.number_of_seats = rez

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
        # if sum(rez.values()) < hall.number_of_seats:
        #     rez['Uncategorized'] = hall.number_of_seats - sum(rez.values())
        # a = 2
        return rez
