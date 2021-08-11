# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import models, fields, api


class Ticket(models.Model):
    _name = 'cinema.ticket'
    _description = 'cinema.ticket'

    number = fields.Char(string="Ticket's number", readonly=True, required=True, copy=False, default='New')
    visitor_id = fields.Many2one('res.partner')
    cinema_movie_show_id = fields.Many2one('cinema.movie_show', string='Cinema movie show', required=True)

    date_start = fields.Datetime(
        'Date start',
        related='cinema_movie_show_id.date_start',
        readonly=True
    )
    date_stop = fields.Datetime(
        'Date stop',
        related='cinema_movie_show_id.date_stop',
        readonly=True
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (number)',
         'Number must be unique.')
    ]

    @api.model
    def create(self, vals):
        if vals.get('number', 'New') == 'New':
            vals['number'] = self.env['ir.sequence'].next_by_code(
                'cinema.ticket') or 'New'
        result = super(Ticket, self).create(vals)
        if result.cinema_movie_show_id.cinema_hall_id.number_of_seats < self.search_count(
                [('cinema_movie_show_id', '=', result.cinema_movie_show_id.id)]):
            raise UserError('The hall is full')
        return result

    def name_get(self):
        result = []
        for record in self:
            rec_name = "%s > %s > %s (%s) > %s" % (record.number,
                                                   record.cinema_movie_show_id.cinema_hall_id.cinema_id.name,
                                                   record.cinema_movie_show_id.cinema_hall_id.name,
                                                   record.date_start,
                                                   record.cinema_movie_show_id.movie_id.name)
            result.append((record.id, rec_name))
        return result


class Search(models.Model):
    _inherit = 'res.partner'
    tickets_count = fields.Integer(
        string='Tickets',
        compute='_compute_amount_of_tickets',
        store=False,
    )

    def _compute_amount_of_tickets(self):
        for person in self:
            amount = self.env['cinema.ticket'].search_count([('visitor_id', '=', person.id)])
            person.tickets_count = amount
