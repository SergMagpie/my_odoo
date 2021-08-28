from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging  #Get the logger

_logger = logging.getLogger(__name__) #Get the logger


class AccountInvoicePo(models.Model):
    _inherit = "account.invoice"

    def _prepare_invoice_line_from_po_line(self, line):
        vals = super(AccountInvoicePo, self)._prepare_invoice_line_from_po_line(line)
        vals['markup'] = line.discount
        return vals



class AccountAnalyticAccountOpportunity(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    @api.depends('opportunity_ids.analytic_account_id')
    def _set_opprtunity(self):
        for rec in self:
            for opp in rec.opportunity_ids:
                rec.opportunity_id = opp.id

    @api.multi
    def _compute_expenses_count(self):
        for r in self:
            x = 0.0
            y = []
            exp = self.env['hr.expense'].search([('analytic_account_id', '=', r.id)])
            for rec in exp:
                if rec.state not in ['cancel', 'submit']:
                    x += rec.total_amount
                    y.append(rec.id)
            r.expense_count = x
            return y

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
    def action_view_all_picking(self):
        for rec in self:
            picking_list = []
            for so in rec.quotations_ids:
                if so.state != 'cancel':
                    for out_picking in so.picking_ids:
                        picking_list.append(out_picking.id)
            for rfq in rec.rfq_ids:
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

            for s in rec.quotations_ids:
                for i in s.invoice_ids:
                    invoices_list.append(i.id)
            for p in rec.rfq_ids:
                for i in p.invoice_ids:
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
            for s in rec.rfq_ids:
                po_list.append(s.id)
                if s.state != 'cancel':
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
    def action_view_all_so(self):
        for rec in self:
            so_list = []
            x = 0
            for s in rec.quotations_ids:
                so_list.append(s.id)
                if s.state != 'cancel':
                    x += 1
            domain = [('id', '=', so_list)]
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Related Qoutations'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'target': 'current',
                'domain': domain,
            }
            rec.all_so_count = x
            return action

    @api.multi
    @api.depends('agents_ids.name', 'po_line.original_price', 'po_line.product_qty', 'other', 'rate')
    def _amount_commission(self):
        for r in self:
            x = 0.0
            total = 0.0
            # exp = 0.0
            y = 0.0
            for agent in r.agents_ids:
                x += agent.commission.fix_qty
            if x:
                for line in r.po_line:
                    if line.order_state not in ['cancel']:
                        total += line.original_price * line.product_qty
                if total != 0:
                    y = (100 - x) / 100
                    if y != 0:
                        y = total / y
                    y = y - total
                    y = (y * 100) / total
            r.bonus = y
            r.commission_total = x

    @api.multi
    @api.depends('po_line.price_subtotal', 'po_line.original_price', 'other', 'so_line.discount', 'use_nds', 'rate',
                 'po_line.nds', 'po_line.call_of_duty', 'po_line.other_markup', 'po_line.fare_to_client',
                 'po_line.discount', 'po_line.duty', 'quotations_ids.amount_total', 'rfq_ids.amount_total',
                 'so_line.agents.amount', 'po_line.markup', 'po_line.bonus', 'commission_total')
    def _amount_all(self):
        for r in self:
            mark = 0.0
            duty = 0.0
            tax = 0.0
            mark_2 = 0.0
            so = 0.0
            base = 0.0
            disc = 0.0
            so_disc = 0.0
            f_t_c = 0.0
            fare_line = 0.0
            bonus = 0.0
            comm = 0.0
            for rfq_line in r.po_line:
                if rfq_line.order_state not in ['cancel']:
                    price = (rfq_line.price_unit / 100) * rfq_line.product_qty
                    line_disc = price * rfq_line.discount
                    disc += line_disc
                    line_so = rfq_line.original_price * rfq_line.product_qty
                    so += line_so
                    comm += r.commission_total * (line_so / 100)
                    bonus += rfq_line.bonus * (line_so / 100)
                    so_price = (rfq_line.soline.price_unit / 100) * rfq_line.soline.product_uom_qty
                    so_disc += so_price * rfq_line.soline.discount
                    # base += (rfq_line.price_unit - line_disc) * rfq_line.product_qty
                    base += rfq_line.price_unit * rfq_line.product_qty
                    # po += rfq_line.price_unit * rfq_line.product_qty
                    # RKB MARKUP
                    line_mark = price * rfq_line.markup
                    mark += line_mark
                    sum_price = (rfq_line.price_unit * rfq_line.product_qty) + line_mark
                    if r.other:
                        # OTHER DUTY
                        duty_price = sum_price / 100
                        line_duty = duty_price * rfq_line.call_of_duty
                        duty += line_duty
                        sum_price += line_duty
                        if r.use_nds:
                            # OTHER TAXes
                            tax_price = sum_price / 100
                            line_tax = tax_price * rfq_line.nds
                            tax += line_tax
                            sum_price += line_tax
                    # RKB FARE
                    sum_price += rfq_line.duty * rfq_line.product_qty
                    fare_line += rfq_line.duty * rfq_line.product_qty
                    if r.other:
                        # OTHER MARKUP
                        mark2_price = sum_price / 100
                        line_mark2 = mark2_price * rfq_line.other_markup
                        mark_2 += line_mark2
                        f_t_c += rfq_line.fare_to_client * rfq_line.product_qty
            r.discount_total = disc
            r.fare_total = fare_line
            z = base + fare_line - disc
            r.additional_total = base - disc
            r.po_amount_total = z
            margin_so = so - duty - tax - f_t_c - comm
            perc = 0.0
            r.margin_total = margin_so - z
            if z != 0:
                perc = (margin_so / z) * 100
            r.margin_total_percent = perc - 100
            if r.other:
                if r.rate != 0:
                    so_disc = so_disc * r.rate
                    mark = mark * r.rate
                    duty = duty * r.rate
                    bonus = bonus * r.rate
                    if r.use_nds:
                        tax = tax * r.rate
                    mark_2 = mark_2 * r.rate
                    so = so * r.rate
                    f_t_c = f_t_c * r.rate
            r.so_amount_total = so
            r.markup_total = mark
            r.duty_total = duty
            r.total_nds = tax
            r.total_bonus = bonus

            r.total_other_markup = mark_2
            r.total_fare_to_client = f_t_c
            r.so_discount_total = so_disc
            r.total_partner_account = tax + mark_2 + f_t_c + duty

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
    quotations_ids = fields.One2many('sale.order', 'analytic_account_id', string='Quotations list')
    rfq_ids = fields.One2many('purchase.order', 'analytic_account_id', string='RFQs list')

    all_so_count = fields.Integer(compute=action_view_all_so, string=_('Quotatations'))
    all_invoice_count = fields.Integer(compute=action_view_all_invoices, string=_('Invoices'))
    all_po_count = fields.Integer(compute=action_view_all_po, string=_('RFQ'))
    all_transfers_count = fields.Integer(compute=action_view_all_picking, string=_('Transfers'))
    expense_count = fields.Monetary(compute=_compute_expenses_count)
    order_list_ids = fields.One2many(related='opportunity_id.order_list_ids',
                                     string=_('Order list'))
    so_line = fields.One2many('sale.order.line', 'control_id',
                              string='Quotations')
    po_line = fields.One2many('purchase.order.line', 'control_id', string='RFQs')
    po_line2 = fields.One2many(related='po_line')
    analogue_order_list_ids = fields.One2many('sale.analouge.order.list',
                                              'control_id',
                                              string='Analogue Order list')
    all_markup = fields.Float(_('Set Markup'), default=1.0)
    all_discount = fields.Float(_('Set Discount'))
    duty = fields.Float(_('Set Fare'))

    other = fields.Boolean(_('Use other Companies'), default=False)
    use_nds = fields.Boolean(_('Use TAX'), default=False)

    other_company_id = fields.Many2one('res.company', string=_('Related company'))

    other_currency_id = fields.Many2one('res.currency', string=_('Currency'))
    nds = fields.Float(_('TAX (%)'))
    rate = fields.Float(string=_('Rate to EUR'), default=1.0)
    other_markup = fields.Float(_('Markup (coeff)'))
    fare_to_client = fields.Float(string=_('Fare'))
    bonus = fields.Float(_('Bonus (%)'), store=True, compute=_amount_commission)

    po_amount_total = fields.Float(string=_('Total'), store=True, compute=_amount_all)
    so_amount_total = fields.Float(string=_('Total'), store=True, compute=_amount_all)
    additional_total = fields.Float(string=_('Total'), store=True, compute=_amount_all)
    margin_total = fields.Float(string=_('Margin Total'), store=True, compute=_amount_all)
    margin_total_percent = fields.Float(string=_('%'), store=True, compute=_amount_all)

    discount_total = fields.Float(string=_('Discount '), store=True, compute=_amount_all)
    markup_total = fields.Float(string=_('Markup '), store=True, compute=_amount_all)
    duty_total = fields.Float(string=_('Duty '), store=True, compute=_amount_all)
    fare_total = fields.Float(string=_('Fare '), store=True, compute=_amount_all)

    so_discount_total = fields.Float(string=_('Discount '), store=True, compute=_amount_all)
    total_nds = fields.Float(string=_('TAX '), store=True, compute=_amount_all)
    total_fare_to_client = fields.Float(string=_('Fare'), store=True, compute=_amount_all)
    total_bonus = fields.Float(string=_('Bonus '), store=True, compute=_amount_all)
    total_other_markup = fields.Float(string=_('Markup '), store=True, compute=_amount_all)
    total_partner_account = fields.Float(string=_('Total '), store=True, compute=_amount_all)

    agents_ids = fields.Many2many('res.partner', string='Agents', domain="[('agent', '=', True)]")

    commission_total = fields.Float(string=_('Commission '), store=True, compute=_amount_commission)

    #RFQ mass actions

    @api.multi
    @api.onchange('other')
    def onchange_other(self):
        for r in self:
            if not r.other:
                r.other_company_id = False

    @api.multi
    @api.onchange('other_company_id')
    def onchange_other_company_id(self):
        for r in self:
            r.other_currency_id = r.other_company_id.currency_id.id
            r.rate = r.other_company_id.currency_id.rate

    @api.multi
    @api.onchange('all_markup')
    def set_rkb_mark_up(self):
        for rec in self:
            for r in rec.po_line:
                if r.order_state not in ['done', 'cancel']:
                    # r.markup = (rec.all_markup * 100) - 100
                    r.markup = rec.all_markup

    @api.multi
    @api.onchange('other_markup')
    def set_other_mark_up(self):
        for rec in self:
            for r in rec.po_line:
                if r.order_state not in ['done', 'cancel']:
                    r.other_markup = (rec.other_markup * 100) - 100

    @api.multi
    @api.onchange('all_discount')
    def set_rkb_discount(self):
        for rec in self:
            for r in rec.po_line:
                if r.order_state not in ['done', 'cancel']:
                    r.discount = rec.all_discount

    @api.multi
    @api.onchange('nds')
    def set_other_tax(self):
        for rec in self:
            for r in rec.po_line:
                if r.order_state not in ['done', 'cancel']:
                    r.nds = rec.nds

    @api.multi
    @api.onchange('duty')
    def set_rkb_fare(self):
        for rec in self:
            tot_weight = 0.0
            rec_count = 0
            for r in rec.po_line:
                if r.order_state not in ['done', 'cancel']:
                    tot_weight += r.product_id.weight * r.product_qty
                    rec_count += r.product_qty

            if rec.duty != 0.0:
                if tot_weight == 0.0:
                    x = rec.duty / rec_count
                    for r in rec.po_line:
                        if r.order_state not in ['done', 'cancel']:
                            r.duty = x
                else:
                    x = rec.duty / tot_weight
                    for r in rec.po_line:
                        if r.order_state not in ['done', 'cancel']:
                            r.duty = r.product_id.weight * x

            if rec.duty == 0.0:
                for r in rec.po_line:
                    if r.order_state not in ['done', 'cancel']:
                        r.duty = 0.0

    @api.multi
    @api.onchange('fare_to_client')
    def set_customer_fare(self):
        for rec in self:
            tot_weight = 0.0
            rec_count = 0
            for r in rec.po_line:
                if r.order_state not in ['done', 'cancel']:
                    tot_weight += r.product_id.weight * r.product_qty
                    rec_count += r.product_qty

            if rec.fare_to_client != 0.0:
                if tot_weight == 0.0:
                    x = rec.fare_to_client / rec_count
                    if rec.rate != 0:
                        x = x / rec.rate
                    for r in rec.po_line:
                        if r.order_state not in ['done', 'cancel']:
                            r.fare_to_client = x
                else:
                    x = rec.fare_to_client / tot_weight
                    if rec.rate != 0:
                        x = x / rec.rate
                    for r in rec.po_line:
                        if r.order_state not in ['done', 'cancel']:
                            r.fare_to_client = r.product_id.weight * x

            if rec.fare_to_client == 0.0:
                for r in rec.po_line:
                    if r.order_state not in ['done', 'cancel']:
                        r.fare_to_client = 0.0

    @api.multi
    def action_set_duty(self):
        for r in self:
            for rec in r.po_line:
                if rec.order_state not in ['done', 'cancel']:
                    rec.call_of_duty = rec.product_id.rkb_item_type.duty

    @api.multi
    def action_clear_duty(self):
        for r in self:
            for rec in r.po_line:
                if rec.order_state not in ['done', 'cancel']:
                    rec.call_of_duty = 0.0

    @api.multi
    def mass_action_update_sale_order(self):
        for rec in self:
            if rec.rfq_ids:
                for rfq in rec.rfq_ids:
                    rfq.action_update_sale_order()

    @api.multi
    def action_set_date_so_line(self):
        for rec in self:
            ctx = {
                'aaa_id': rec.id
            }
            return {
                'name': _('Set Date Planned'),
                'res_model': 'sale.order.line.mass.action.wizard',
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': ctx
            }
