# -*- coding: utf-8 -*-

import re
# import requests

from requests import HTTPError, ConnectionError, post, get
import json
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging  # Get the logger
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)  # Get the logger


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    @api.depends('version')
    def get_ver(self):
        for r in self:
            r.display_version = 'v' + str(r.version) + '.0'

    state = fields.Selection([
        ('draft', (_('RFQ'))),
        ('sent', (_('RFQ Sent'))),
        ('to approve', (_('To Approve'))),
        ('received', (_('RFQ Received'))),
        ('so_updated', (_('SO Updated'))),
        ('purchase', (_('Purchase Order'))),
        ('done', (_('Locked'))),
        ('cancel', (_('Cancelled')))],
        string=_('Status'),
        readonly=True,
        index=True,
        copy=False,
        default='draft',
        track_visibility='onchange')

    version = fields.Integer(_('Ver.:'), default=1, copy=False)
    display_version = fields.Char(_('Version'), compute=get_ver, store=True)

    parent_id = fields.Many2one('purchase.order', string=_('Last version'), copy=False, readonly=True)
    parent_left = fields.Integer(copy=False)
    parent_right = fields.Integer(copy=False)
    child_ids = fields.One2many('purchase.order', 'parent_id', string=_('Previous versions'), copy=False)
    rkb_customer_code = fields.Char(string=_('Customer code'))
    rkb_quote_number = fields.Char(_('RFQ Number From RKB'))
    rkb_date = fields.Char(_('Date'))
    all_markup = fields.Float(_('Set Markup'))
    all_discount = fields.Float(_('Set Discount'))
    rkb_final_customer = fields.Many2one(related='sale_id.partner_id',
                                         store=True,
                                         string=_('Final Customer'),
                                         readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string=_('Contract/Analytic'),
                                          ondelete="cascade", auto_join=True, copy=True)
    rkb_crm = fields.Char(_('CRM'))
    rkb_operator = fields.Char(_('Operator'))
    sale_id = fields.Many2one('sale.order', _('Sale Order'))
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    rfq_unique_id = fields.Char()
    token = fields.Char()
    result = fields.Text()
    last_result_datetime = fields.Datetime(string='Last result')

    date_planned = fields.Datetime(string='Scheduled Date', compute='_compute_date_planned', store=True, index=True, default=fields.Datetime.to_string(fields.datetime.now() + timedelta(days=1)))

    @api.multi
    def get_data_from(self):
        for rec in self:
            log = 'Start ====>' + '\n\n'
            login, password = self.env['rkb.config.settings.container'].get_keys()
            # urls
            url = 'https://crm.rkbbearings.com/webservice.php?operation=gettoken&username=' + str(
                login) + '&password=' + str(password)

            url2 = 'https://crm.rkbbearings.com/webservice.php?operation=datidisp'
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            # get token
            response = get(url, auth=None, headers=headers)
            _logger.info('\n\n\n\n---------------- response, %s \n\n\n\n', response)

            y = json.loads(response.text)
            _logger.info('\n\n\n\n---------------- y, %s \n\n\n\n', y)

            log += 'response: ' + str(y) + '\n\n'
            result = y['result']

            token = result['tokenKey']
            _logger.info('\n\n\n\n---------------- token, %s \n\n\n\n', token)

            log += 'token: ' + token + '\n\n'
            rec.token = token
            # Set data
            quotes = {}
            quotes['generatedKey'] = token
            quotes['action'] = 'QUOTES'
            z = []

            for line in rec.order_line:
                if line.product_id.name == 'undefined_product':
                    product = line.ordered_product_name.name
                else:
                    product = line.product_id.name
                element = {
                    "rfq_line_unique_id": line.unique_id,
                    "rfq_unique_id": rec.rfq_unique_id,
                    "customer_product_code": product,
                    "item_qty": line.product_qty,
                    "item_brand": line.ordered_product_brand_name.name,
                    "notes": line.rkb_description,
                }
                z.append(element)
            data = {
                'generatedKey': token,
                'action': 'QUOTES',
                'element': json.dumps(z),
            }
            log += 'data: ' + str(data) + '\n\n'
            # Send request
            log += 'url_request: ' + url2 + '\n\n'
            _logger.info('\n\n\n\n---------------- data, %s \n\n\n\n', data)

            response3 = post(url2, data=data)
            _logger.info('\n\n\n\n---------------- response3, %s \n\n\n\n', response3)

            y = json.loads(response3.text)
            _logger.info('\n\n\n\n---------------- y, %s \n\n\n\n', y)

            log += 'response: ' + str(response3) + '==>' + str(y) + '\n\n'
            rec.result = log + '====> Done' + ' ======> ' + str(
                datetime.now().strftime('%H:%M:%S'))
            if 'success' in y:
                if y['success']:
                    rec.state = 'sent'
            _logger.info('\n\n\n\n---------------- DONE \n\n\n\n')
        self = self.with_context(send_rfq=True)
        return self.action_rfq_send()

    @api.model
    def update_purchase_order_line_from_rkbbearings(self):
        rfq_ids = self.env['purchase.order'].search([('state', '=', 'sent')])
        for rec in rfq_ids:
            rec.check_data_from()

    @api.multi
    def product_product_search_create(self, code):
        if not code:
            product = self.env['ir.model.data'].get_object('sale_flow', 'product_product_0').id
        else:
            product = self.env['product.product'].search([('name', '=', code)], limit=1).id
            if not product:
                product = self.env['product.product'].create({
                    'name': code,
                    'type': 'product',
                    'purchase_ok': True,
                    'sale_ok': True,
                }).id
        return product

    @api.multi
    def update_target_rfq(self, rfq, data):
        if data.get('CUSTOMER_CODE'):
            rfq.rkb_customer_code = data['CUSTOMER_CODE']
        if data.get('RKB_QUOTATION_NUMBER'):
            rfq.rkb_quote_number = data['RKB_QUOTATION_NUMBER']
        if data.get('FINAL_CUSTOMER1'):
            rkb_final_customer = self.env['res.partner'].search(
                [('customer_number', '=', data['FINAL_CUSTOMER1'])], limit=1)
            rfq.rkb_final_customer = rkb_final_customer.id
        elif data.get('FINAL_CUSTOMER2'):
            rkb_final_customer = self.env['res.partner'].search(
                [('customer_number', '=', data['FINAL_CUSTOMER2'])], limit=1)
            rfq.rkb_final_customer = rkb_final_customer.id

        return rfq

    @api.multi
    def update_order_line_from_data(self, line, data):
        line.rkb_description = data['NOTES']
        line.price_unit = data['UNIT_PRICE']
        declined = data['DECLINED'].replace(' ', '')
        if declined == 'T':
            line.is_declined = True
            line.decline_reason = data['DECLINED_DESCRIPTION']
        _logger.info('\n +++++++++++ ALTERNATIVE, %s', '.' + data['ALTERNATIVE'] + '.')
        alternative = data['ALTERNATIVE'].replace(' ', '')
        if alternative == 'T':
            line.has_alternatives = True
            _logger.info('\n +++++++++++ line.has_alternatives, %s', line.has_alternatives)
        line.discount = data['DISCOUNT1']
        return line

    @api.multi
    def check_data_from(self):
        login, password = self.env['rkb.config.settings.container'].get_keys()
        for rec in self:
            if rec.rfq_unique_id:
                url = 'https://crm.rkbbearings.com/webservice.php?operation=autdisp&username={username}&password={password}&rfq_unique_id={rfq_unique_id}' \
                    .format(username=login, password=password, rfq_unique_id=rec.rfq_unique_id)
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }
                response = get(url, auth=None, headers=headers)
                try:
                    data = response.json()
                    _logger.info("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO data %s", data)
                except json.JSONDecodeError as error:
                    log = '\n\n result:' + str(error) + '\n\n'
                else:
                    log = '\n\n result:' + str(data) + '\n\n'
                    result = data['result']['dati']
                    _logger.info("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO result %s", result)
                    if result:
                        rec.update_target_rfq(rec, result[0])
                        rec.state = 'received'
                        for order_line_values in result:
                            if order_line_values['RFQ_LINE_UNIQUE_ID']:
                                order_line = rec.order_line.search(
                                                              [('unique_id', '=', order_line_values['RFQ_LINE_UNIQUE_ID'])])
                                if order_line:
                                    if order_line_values['DECLINED'] == 'F':
                                        product_product = self.product_product_search_create(
                                                                                    order_line_values['ITEM_EXTENDED_CODE'])
                                        order_line.product_id = product_product
                                        order_line.ordered_product_brand_name = rec._default_rkb_vendor_id()
                                    self.update_order_line_from_data(order_line, order_line_values)
                                else:
                                    continue
                            else:
                                product_product = self.product_product_search_create(
                                                                                    order_line_values['ITEM_EXTENDED_CODE'])
                                brand = rec._default_rkb_vendor_id()
                                order_line = self.env['purchase.order.line'].new({
                                    'product_id': product_product,
                                    'name': order_line_values['ITEM_EXTENDED_CODE'],
                                    'rkb_product_position': order_line_values['POS'],
                                    'ordered_product_brand_name': brand,
                                    'order_id': rec.id,
                                    'product_qty': order_line_values['ITEM_QTY'],
                                })
                                order_line.onchange_product_id()
                                order_line = order_line._convert_to_write(order_line._cache)
                                order_line = self.env['purchase.order.line'].create(order_line).id
                                order_line = self.env['purchase.order.line'].browse(order_line)
                                self.update_order_line_from_data(order_line, order_line_values)
                rec.result += log + '====> Done' + ' ======> ' + str(datetime.now().strftime('%H:%M:%S'))
                rec.last_result_datetime = fields.Datetime.now()

    @api.multi
    def set_markup(self):
        for r in self:
            for rec in r.odrder_line:
                rec.markup = r.all_markup

    @api.multi
    def set_discount(self):
        for r in self:
            for rec in r.order_line:
                rec.discount = r.all_discount

    @api.onchange('sale_id')
    def create_po_from_so_sale_order_id_onchange(self):
        if self.sale_id:
            self.origin = self.sale_id.name
        else:
            self.origin = None

    @api.multi
    def action_new_ver_sale_order(self):
        for rec in self:
            rec.sale_id.new_ver = True
            new_so = rec.sale_id.copy()
            new_so.version = rec.sale_id.version + 1
            new_so.analytic_account_id = rec.analytic_account_id.id
            rec.sale_id.parent_id = new_so.id
            for r in rec.sale_id.child_ids:
                r.parent_id = new_so.id
            rec.sale_id.action_cancel()
            rec.sale_id = new_so.id
            rec.action_update_sale_order()
            form_view = self.env.ref('sale.view_order_form')
            return {
                'name': _('New Version of Quotation'),
                'res_model': 'sale.order',
                'res_id': new_so.id,
                'views': [(form_view.id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'inline'
            }

    @api.multi
    def action_new_version(self):
        for rec in self:
            new_po = rec.copy()
            new_po.version = rec.version + 1
            rec.parent_id = new_po.id
            for r in rec.child_ids:
                r.parent_id = new_po.id
            rec.button_cancel()
            form_view = self.env.ref('purchase.purchase_order_form')
            return {
                'name': _('New Version of RFQ'),
                'res_model': 'purchase.order',
                'res_id': new_po.id,
                'views': [(form_view.id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'inline'
            }

    def create_sale_order_line(self, purchase_order_line):

        if self.analytic_account_id.other and self.analytic_account_id.rate != 0:
            price_unit = purchase_order_line.original_price * self.analytic_account_id.rate
        else:
            price_unit = purchase_order_line.original_price

        so_line = {
            'order_id': self.sale_id.id,
            'product_id': purchase_order_line.product_id.id,
            'name': purchase_order_line.name,
            'product_uom_qty': purchase_order_line.product_qty,
            'price_unit': price_unit,
            'product_uom': purchase_order_line.product_uom.id,
            'internal_notes': purchase_order_line.internal_notes,
            'rkb_product_position': purchase_order_line.rkb_product_position,
            'ordered_product_name': purchase_order_line.ordered_product_name.id,
            'ordered_product_brand_name': self._default_rkb_vendor_id(),
        }

        return so_line

    @api.multi
    def action_update_sale_order(self):
        zero_product = self.env['ir.model.data'].get_object('sale_flow', 'product_product_0').id
        for r in self:
            if not r.sale_id or not r.sale_id.order_line:
                return
            _logger.info("zzzzzzzzzzzzzzzzzz r.sale_id.order_line %s", r.sale_id.order_line)
            r.sale_id.order_line.unlink()

            sale_order_fields = r.update_sale_order_fields()

            if sale_order_fields:
                r.sale_id.write(sale_order_fields)

            for line in self.order_line:
                if line.is_declined:
                    continue
                if line.product_id.id != zero_product:
                    vals = self.create_sale_order_line(line)
                    soline = self.env['sale.order.line'].create(vals)
                    _logger.info("zzzzzzzzzzzzzzzzzz soline %s", soline)
                    line.soline = soline.id
                    for agent in r.analytic_account_id.agents_ids:
                        soline.agents.create({
                            'object_id': soline.id,
                            'agent': agent.id,
                            'commission': agent.commission.id,
                        })

            r.state = 'so_updated'
            _logger.info("zzzzzzzzzzzzzzzzzz r.state %s", r.state)

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'received', 'so_updated']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.multi
    def button_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'done':
                    raise UserError(
                        _('Unable to cancel purchase order %s as some receptions have already been done.') % (
                            order.name))
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(
                        _("Unable to cancel this purchase order. You must first cancel related vendor bills."))

            # If the product is MTO, change the procure_method of the the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            if order.state in ('draft', 'sent', 'received', 'so_updated', 'to approve'):
                for order_line in order.order_line:
                    if order_line.move_dest_ids:
                        siblings_states = (order_line.move_dest_ids.mapped('move_orig_ids')).mapped('state')
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            order_line.move_dest_ids.write({'procure_method': 'make_to_stock'})

            for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                pick.action_cancel()
        self.write({'state': 'cancel'})

    @api.model
    def _default_rkb_vendor_id(self):
        partner = self.env['ir.model.data'].get_object('sale_flow', 'rkb_switzerland_res_vendor').id
        return partner

    def update_sale_order_fields(self):

        so_field = {
            'rkb_quote_number': self.rkb_quote_number,
            'rkb_date': self.rkb_date,
            'rkb_crm': self.rkb_crm,
            'rkb_operator': self.rkb_operator,

        }
        if self.analytic_account_id.other:
            so_field['company_id'] = self.analytic_account_id.other_company_id.id

        return so_field

    @api.model
    def create(self, vals):
        rfq = super(PurchaseOrder, self).create(vals)
        today = datetime.today().strftime('%Y')
        rfq.rfq_unique_id = str(today) + '_RFQ_' + str(rfq.name) + '-' + str(rfq.id)
        _logger.info('\n\n\n ======> rfq.rfq_unique_id <=======, %s \n\n\n', rfq.rfq_unique_id)
        return rfq

    @api.multi
    def unlink(self):
        for r in self:
            if len(r.child_ids) > 0:
                raise UserError(_('You have to delete all Previous versions.'))
        return super(PurchaseOrder, self).unlink()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('markup', 'price_unit', 'duty', 'call_of_duty',
                 'product_qty', 'nds', 'use_nds', 'other_markup',
                 'fare_to_client', 'other', 'bonus')
    def _compute_sale_price(self):
        for line in self:
            fare = 0
            fare_2 = 0
            markup_2 = 0
            comm = 0.0
            # markup = line.markup * (line.price_unit / 100)
            coeff = line.markup if line.markup else 1
            sale_price = line.price_unit * coeff

            if line.order_id.analytic_account_id.other:
                duty = line.call_of_duty * (sale_price / 100)
                sale_price += duty

                if line.use_nds:
                    tax = line.nds * (sale_price / 100)
                    sale_price += tax

            if line.product_qty != 0:
                fare = line.duty
            sale_price += fare

            if line.order_id.analytic_account_id.other:
                if line.product_qty != 0:
                    fare_2 = line.fare_to_client

                markup_2 = line.other_markup * (sale_price / 100)
            # line.original_price = sale_price + markup_2 + fare_2
            sale_price += markup_2 + fare_2
            comm = line.bonus * (sale_price / 100)
            line.original_price = sale_price + comm


    # @api.depends('duty', 'product_qty')
    # def _compute_amount(self):
    #     for line in self:
    #         super(PurchaseOrderLine, self)._compute_amount()
    #         fare = line.duty * line.product_qty
    #         line.price_subtotal = line.price_subtotal + fare

    @api.onchange('product_id')
    def onchange_product_id(self):
        price = self.price_unit
        qty = self.product_qty
        super(PurchaseOrderLine, self).onchange_product_id()
        self.price_unit = price
        self.product_qty = qty

    call_of_duty = fields.Float(string=_('Duty'), digits=dp.get_precision('Duty'))
    original_price = fields.Float(string='Sale Price', compute=_compute_sale_price)
    markup = fields.Float(string='Markup (coeff)', digits=dp.get_precision('Markup'))
    duty = fields.Float(string='Fare', digits=dp.get_precision('Fare'))
    rkb_description = fields.Char('Description')
    rkb_product_position = fields.Char('#')
    product_qty = fields.Float(digits=(16, 0))
    ordered_product_name = fields.Many2one('analogue.catalogue', string="Name of Analogue")
    ordered_product_brand_name = fields.Many2one('res.partner', string='Brand of Analogue')
    control_id = fields.Many2one(related='order_id.analytic_account_id', string='Contract')
    order_state = fields.Selection(related='order_id.state', string='Quotation state')
    internal_notes = fields.Char(string=_("Seller's notes"))

    use_nds = fields.Boolean(related='order_id.analytic_account_id.use_nds')
    other = fields.Boolean(related='order_id.analytic_account_id.other')

    nds = fields.Float(_('TAX (%)'))
    other_markup = fields.Float(_('Markup (%)'))
    fare_to_client = fields.Float(string=_('Fare to Customer'))
    bonus = fields.Float(_('Bonus (%)'), related='order_id.analytic_account_id.bonus')

    soline = fields.Many2one('sale.order.line')
    agents = fields.One2many(related='soline.agents')
    commission_free = fields.Boolean()
    commission_status = fields.Char(
        compute="_compute_commission_status",
        string="Commission",
    )

    unique_id = fields.Char()

    is_declined = fields.Boolean('Declined', default=False)
    decline_reason = fields.Char('Decline reason')
    has_alternatives = fields.Boolean('Has alternatives', default=False)


    @api.multi
    @api.depends('soline.commission_free', 'soline.agents')
    def _compute_commission_status(self):
        for line in self:
            if line.soline:
                if line.soline.commission_free:
                    line.commission_status = _("Comm. free")
                elif len(line.soline.agents) == 0:
                    line.commission_status = _("No commission agents")
                elif len(line.soline.agents) == 1:
                    line.commission_status = _("1 commission agent")
                else:
                    line.commission_status = _(
                        "%s commission agents"
                    ) % len(line.soline.agents)
            else:
                line.commission_status = _("No related line")

    @api.multi
    def button_edit_agents(self):
        view = self.env.ref(
            'sale_commission.view_sale_commission_mixin_agent_only'
        )
        return {
            'name': _('Agents'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.soline.id,
            'context': self.env.context,
        }

    @api.depends('order_id.order_line')
    def _compute_p_order_line_position(self):
        order_id = self[0].order_id
        for i, line in enumerate(sorted(order_id.order_line, key=lambda l: l.sequence)):
            i += 1
            line.rkb_product_position = '{}{}'.format('0' if i < 10 else '', i)

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['name', 'price_unit']
        if values['order_id'] and values['product_id'] and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.onchange_product_id()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.model
    def create(self, values):
        values.update(self._prepare_add_missing_fields(values))
        line = super(PurchaseOrderLine, self).create(values)
        if line.order_id.state == 'purchase':
            line._create_or_update_picking()
            msg = _("Extra line with %s ") % (line.product_id.display_name,)
            line.order_id.message_post(body=msg)
        if not line.rkb_product_position:
            line._compute_p_order_line_position()
        # Request --- uniq ID
        today = datetime.today().strftime('%Y')
        line.unique_id = str(today) + '_' + str(line.order_id.name) + '_line-' + str(line.id)
        return line

    @api.onchange('rkb_product_position')
    def _rkb_product_position_onchange(self):
        if not self.rkb_product_position:
            return
        product_position = int(re.sub('-', '', self.rkb_product_position))
        if product_position < 10:
            self.rkb_product_position = '{}{}'.format('0', product_position)
        else:
            self.rkb_product_position = str(product_position)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def mail_purchase_order_on_send(self):
        if not self.filtered('subtype_id.internal'):
            order = self.env['purchase.order'].browse(self._context['default_res_id'])
            if order.state in ['draft', 'received', 'so_updated']:
                order.state = 'sent'
                order.get_data_from()
