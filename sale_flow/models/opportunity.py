# -*- coding: utf-8 -*-

import logging  # Get the logger

from odoo import api, fields, models, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)  # Get the logger


class ProductOrderList(models.Model):
    _name = "crm.product.order.list"
    _order = "id"

    @api.multi
    @api.onchange('analogue_id')
    def onchange_analogue_id(self):
        for r in self:
            if r.analogue_id.product_id:
                r.product_id = r.analogue_id.product_id.id

    @api.model
    def _default_anologue_brand(self):
        partner = self.env['ir.model.data'].get_object('sale_flow', 'vendor_is_unknown_res_vendor').id
        return partner

    @api.multi
    @api.depends('opportunity_id.order_list_ids')
    def _compute_product_order_line_position(self):
        opportunity_id = self[0].opportunity_id
        for i, line in enumerate(sorted(opportunity_id.order_list_ids, key=lambda l: l.sequence)):
            i += 1
            line.rkb_product_position = '{}{}'.format('0' if i < 10 else '', i)

    @api.multi
    def _default_sequence(self):
        if not self._context['params'].get('id', False):
            return 1
        opportunity = self.env['crm.lead'].browse(self._context['params']['id'])
        return len(opportunity.order_list_ids) + 1

    sequence = fields.Integer(string='Sequence', default=_default_sequence)
    ordered_product = fields.Char(_('Ordered product'))
    rkb_product_position = fields.Char('#', compute='_compute_product_order_line_position', store=True)

    analogue_id = fields.Many2one('analogue.catalogue', string=_("Code of Analogue"))
    analogue_product_name = fields.Many2one('res.partner', string=_('Brand of Analogue'), default=_default_anologue_brand)
    internal_notes = fields.Char(string=_("Seller's notes"))
    product_id = fields.Many2one('product.product', string=_('RKB Product'))
    qty = fields.Float(_('Quantity'), digits=(16, 0))

    opportunity_id = fields.Many2one('crm.lead')
    so_id = fields.Many2one('sale.order')

    @api.model
    def create(self, vals):
        _logger.info("------------>>>>  vals  <<<<--------------, %s", vals)
        New_id = super(ProductOrderList, self).create(vals)
        product = self.env['product.product'].search([('name', '=', New_id.ordered_product)], limit=1)

        if product:
            partner = self.env['ir.model.data'].get_object('sale_flow', 'rkb_switzerland_res_vendor').id
            new_vals = {
                'product_id': product.id,
                'analogue_product_name': partner,
                'internal_notes': New_id.ordered_product
            }
            New_id.write(new_vals)
        else:
            analogue = self.env['analogue.catalogue'].search([('name', '=', New_id.ordered_product)], limit=1)
            new_vals = {
                'internal_notes': New_id.ordered_product
            }
            if not analogue:
                if not New_id.analogue_product_name:
                    raise Warning(_("Please select Brand of Analogue for: \n%s") % New_id.ordered_product)
                new_anal = analogue.sudo().create({
                    'name': New_id.ordered_product,
                    'analogue_brand': New_id.analogue_product_name.id,
                })
                new_vals['analogue_id'] = new_anal.id
                new_vals['analogue_product_name'] = new_anal.analogue_brand.id
                new_vals['product_id'] = new_anal.product_id.id
            else:
                new_vals['analogue_id'] = analogue.id
                new_vals['analogue_product_name'] = analogue.analogue_brand.id
                new_vals['product_id'] = analogue.product_id.id
            New_id.write(new_vals)

        return New_id


class OpportunityCrmOrderList(models.Model):
    _inherit = "crm.lead"

    @api.multi
    def default_oppor_name(self):
        x = self.env['ir.sequence'].next_by_code('crm.lead')
        return x

    @api.multi
    def action_view_all_picking(self):
        for rec in self:
            picking_list = []
            for so in rec.order_ids:
                if so.state != 'cancel':
                    for out_picking in so.picking_ids:
                        picking_list.append(out_picking.id)
                    for rfq in so.rfq_ids:
                        if rfq.state != 'cancel':
                            for in_picking in rfq.picking_ids:
                                picking_list.append(in_picking.id)
            domain = [('id', '=', picking_list)]
            action = {
                        'type': 'ir.actions.act_window',
                        'name': _('Related Transfers'),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'stock.picking',
                        'target': 'current',
                        'domain': domain,
                    }
            rec.all_transfers_count = len(picking_list)
            return action

    @api.multi
    def action_view_all_invoices(self):
        for rec in self:
            invoices_list = []

            for s in rec.order_ids:
                for i in s.invoice_ids:
                    invoices_list.append(i.id)
            domain = [('id', '=', invoices_list)]
            action = {
                        'type': 'ir.actions.act_window',
                        'name': _('Related Invoices'),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'account.invoice',
                        'target': 'current',
                        'domain': domain,
                    }
            rec.all_invoice_count = len(invoices_list)
            return action

    @api.multi
    def action_view_all_po(self):
        for rec in self:
            po_list = []
            x = 0
            for s in rec.order_ids:
                for p in s.rfq_ids:
                    po_list.append(p.id)
                    if p.state != 'cancel':
                        x += 1
            domain = [('id', '=', po_list)]
            action = {
                        'type': 'ir.actions.act_window',
                        'name': _('Related RFQ'),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'purchase.order',
                        'target': 'current',
                        'domain': domain,
                    }
            rec.all_po_count = x
            return action

    @api.multi
    def button_add_products(self):
        for rec in self:
            ctx = {
                'lead_id': rec.id
            }
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Add Products'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'crm.product.order.list.wizard',
                'target': 'new',
                'context': ctx,
            }
            return action

    @api.multi
    @api.depends('order_ids.amount_total', 'order_ids.state')
    def compute_total_revenue(self):
        for r in self:
            x = 0.0
            for rec in r.order_ids:
                if rec.state != 'cancel':
                    x += rec.amount_total
            r.planned_revenue = x

    name = fields.Char('Opportunity', required=True, index=True, default=default_oppor_name)

    analytic_account_id = fields.Many2one('account.analytic.account', string=_('Contract/Analytic'),
                                          ondelete="cascade", auto_join=True)
    all_invoice_count = fields.Integer(compute=action_view_all_invoices, string=_('Invoices'))
    all_po_count = fields.Integer(compute=action_view_all_po, string=_('RFQ'))
    all_transfers_count = fields.Integer(compute=action_view_all_picking, string=_('Transfers'))
    order_list_ids = fields.One2many('crm.product.order.list',
                                     'opportunity_id',
                                     string=_('Order list'),
                                     ondelete='cascade')

    rkb_customer_aim = fields.Many2one('rkb.lead.customer.aim', _('Customer aim'))

    # Customer quotations
    create_date = fields.Datetime(_('Quotation date'), readonly=True)
    date_deadline = fields.Date(_('Quotation deadline'), help=_("Estimate of the date on which the opportunity will be won."))
    rkb_customer_executive = fields.Many2one('res.users',
                                             _('Curator'))

    planned_revenue = fields.Float(_('Total deal margin'),
                                   track_visibility='always',
                                   compute=compute_total_revenue,
                                   store=True)
    # Bonuses
    rkb_manager_bonus = fields.Char(_('Manager bonus'))
    rkb_curator_bonus = fields.Char(_('Curator bonus'))
    rkb_customer_bonus = fields.Char(_('Customer bonus'))
    partner_id = fields.Many2one(domain=[('customer', '=', True)])
    actual_revenue = fields.Monetary(_('Actual Cost/Revenue'),
                                     related='analytic_account_id.balance')

    currency_id = fields.Many2one(related="company_id.currency_id", string=_("Currency"), readonly=True)
    company_id = fields.Many2one('res.company', string=_('Company'), required=True,
                                 default=lambda self: self.env.user.company_id)

    expense_count = fields.Monetary(compute='_compute_expenses_count')

    def _compute_expenses_count(self):
        for r in self:
            x = 0.0
            y = []
            if r.analytic_account_id:
                exp = self.env['hr.expense'].search([('analytic_account_id', '=', r.analytic_account_id.id)])
                for rec in exp:
                    if rec.state not in ['cancel', 'submit']:
                        x += rec.total_amount
                        y.append(rec.id)
                r.expense_count = x
            return y

    @api.multi
    def action_create_so(self):
        if not self.partner_id:
            raise Warning(_("Please, choose a customer"))
        so = self.env['sale.order'].sudo().create({
            'partner_id': self.partner_id.id,
            'team_id': self.team_id.id,
            'opportunity_id': self.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'user_id': self.user_id.id,
            'curator_id': self.rkb_customer_executive.id,
            'analytic_account_id': self.analytic_account_id.id,
        })
        _logger.info("------------>>>>  Qoutation created  <<<<--------------: %s", so.opportunity_id.id)
        prod = self.env['ir.model.data'].get_object('sale_flow', 'product_product_0').id
        for rec in self.order_list_ids:
            if rec.product_id and rec.product_id.id != prod:
                line = self.env['sale.order.line'].sudo().create({
                    'original_sequence_from_lead': rec.id,
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.qty,
                    'order_id': so.id,
                    'product_uom': rec.product_id.uom_id.id,
                    # 'ordered_product_name': rec.analogue_id.id,
                    'internal_notes': rec.internal_notes,
                    'ordered_product_brand_name': rec.analogue_product_name.id,
                    'price_unit': rec.product_id.option_price_first
                })
                _logger.info("------------>>>>  Line created  <<<<--------------: %s", line.id)
            else:
                analogue_line = self.env['sale.analouge.order.list'].sudo().create({
                    'original_sequence_from_lead': rec.id,
                    'analogue_id': rec.analogue_id.id,
                    'internal_notes': rec.internal_notes,
                    'qty': rec.qty,
                    'so_id': so.id,
                    'product_id': rec.product_id.id,
                  })
                _logger.info("------------>>>>  Analogue Line created  <<<<--------------: %s", analogue_line.id)

    @api.multi
    def expense_view(self):
        self.ensure_one()
        domain = self._compute_expenses_count()
        return {
                'name': _('Documents'),
                'domain': [('id', 'in', domain)],
                'res_model': 'hr.expense',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'limit': 80,
               }

    @api.multi
    def get_document_emails(self):
        for rec in self:
            sale_orders_list = []

            invoices_list = []
            purchase_orders_list = []
            for s in rec.order_ids:
                sale_orders_list.append(s.id)
                for p in s.rfq_ids:
                    purchase_orders_list.append(p.id)
                for i in s.invoice_ids:
                    invoices_list.append(i.id)

            domain = ["&", ["message_type", "=", "comment"], "|", "|", "|",
                      "&", ["res_id", "=", rec.id], ["model", "=", "crm.lead"],
                      "&", ["model", "=", "sale.oder"], ["res_id", "in", sale_orders_list],
                      "&", ["model", "=", "purchase.order"], ["res_id", "in", purchase_orders_list],
                      "&", ["model", "=", "account.invoice"], ["res_id", "in", invoices_list]]

            action = {
                        'type': 'ir.actions.act_window',
                        'name': _('Related Emails'),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'mail.message',
                        'target': 'current',
                        'domain': domain,
                    }
            return action

    @api.multi
    def write(self, vals):
        if 'type' in vals and vals['type'] == 'opportunity':
            a, b = self.name.split('-')
            if a == 'LE':
                a = 'OP'
                vals['name'] = str(a) + '-' + str(b)
                ma_name = 'MA(' + vals['name'] + ')'
                contract = self.env['account.analytic.account'].create({'name': ma_name})
                vals['analytic_account_id'] = contract.id
                contract.opportunity_id = self.id
                if 'partner_id' in vals:
                    contract.partner_id = vals['partner_id']
        if 'partner_id' in vals and self.analytic_account_id:
            self.analytic_account_id.partner_id = vals['partner_id']

        return super(OpportunityCrmOrderList, self).write(vals)

    @api.model
    def create(self, vals):
        New_iD = super(OpportunityCrmOrderList, self).create(vals)
        if New_iD.type == 'lead':
            New_iD.name = 'LE' + '-' + str(New_iD.name)
        if New_iD.type == 'opportunity':
            New_iD.name = 'OP' + '-' + str(New_iD.name)
            aaa_vals = {
                'name': New_iD.name,
                'partner_id': New_iD.partner_id.id,
            }
            if New_iD.partner_id and New_iD.partner_id.all_markup:
                aaa_vals['all_markup'] = New_iD.partner_id.all_markup
            company_id = self.env.context.get('company_id') or self.env.user.company_id.id
            company = self.env['res.company'].browse(company_id)
            if company_id:
                aaa_vals['company_id'] = company_id
            if company and company.parent_id:
                aaa_vals['other'] = True
            contract = self.env['account.analytic.account'].create(aaa_vals)
            New_iD.analytic_account_id = contract.id
            contract.opportunity_id = New_iD.id
        return New_iD
