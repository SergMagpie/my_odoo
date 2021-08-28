# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    @api.onchange('name')
    def rkb_name_onchange(self):
        if self.name:
            self.name = self.name.strip()

    @api.onchange('email')
    def rkb_email_onchange(self):
        if self.email:
            self.email = self.email.strip()


    # @api.model
    # def create(self, vals):
    #     domain = []
    #
    #     # if vals['email']:
    #     #     domain.extend(('|', ('email', '=', vals['email'])))
    #
    #     domain.append(('name', '=', vals['name']))
    #
    #     duplicate_partner = self.search_count(domain)
    #
    #     if duplicate_partner:
    #         raise UserError(_('Name and Email must be unique for Customer'))
    #     return super().create(vals)

    name = fields.Char(index=True, translate=True)
    company_name = fields.Char('Company Name', translate=True)

    customer_number = fields.Char('Customer code', compute='get_customer_code', store=True, copy=False)

    temp_customer_number = fields.Char('Customer code', readonly=True, store=True, copy=False)

    rkb_bank_account_number = fields.Char("Customer's bank account")

    rkb_curator = fields.Many2one('res.users',
                                  string="Seller's curator",
                                  domain=[('share', '=', False)])
    rkb_customer_activity = fields.Many2one('rkb.customer.activity',
                                            string="Status / Customer's activity")
    rkb_department_customer_executive = fields.Many2one('rkb.department.customer.executive',
                                                        string="Department of Customer's executive")
    category_id = fields.Many2many('res.partner.category',
                                   column1='partner_id',
                                   column2='category_id',
                                   string="Customer's status for Seller",
                                   default=_default_category)
    is_driver = fields.Boolean('Driver')

    rkb_delivery_type = fields.Many2one('rkb.delivery.type', string='Delivery Type', ondelete='restrict')
    rkb_delivery_condition = fields.Many2one('rkb.delivery.condition', 'Delivery Condition', default=False)
    all_markup = fields.Float(_('Set Markup'))

    @api.multi
    @api.depends('temp_customer_number', 'country_id')
    def get_customer_code(self):
        for rec in self:
            if rec.country_id and rec.customer and rec.company_type == 'company':
                symbol_code = rec.country_id.code
                rec.customer_number = str(symbol_code) + ' ' + str(rec.temp_customer_number)

    @api.model
    def create(self, vals):
        if vals.get('temp_customer_number', _('New')) == _('New'):
            vals['temp_customer_number'] = self.env['ir.sequence'].next_by_code('res.partner') or _('New')
        res = super(ResPartner, self).create(vals)
        return res
