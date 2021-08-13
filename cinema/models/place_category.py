# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PlaceCategory(models.Model):
    _name = 'cinema.place_category'
    _description = 'cinema.place_category'

    name = fields.Char(string='Place category', required=True)


class AmountPlaces(models.Model):
    _name = 'cinema.amount_places'
    _description = 'cinema.amount_places'

    amount = fields.Integer(required=True, string='amount')
    place_category_id = fields.Many2one('cinema.place_category', required=True)
    cinema_hall_id = fields.Many2one('cinema.hall', required=True)

    # todo create a kanban form for change category
    def name_get(self):
        result = []
        for record in self:
            rec_name = "%s (%s) > %s places" % (
                record.place_category_id.name,
                record.cinema_hall_id.name,
                record.amount
            )
            result.append((record.id, rec_name))
        return result
