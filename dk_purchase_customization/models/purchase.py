from datetime import timedelta, datetime

from odoo import fields, models, api


class Purchase(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Contract',
    )

    use_vendor_currency_rate = fields.Boolean(
        string='Use vendor rate',
        help='Use vendor currency rate'
    )
    vendor_rate = fields.Float(
        digits='Product Price',
    )

    date_order = fields.Datetime(states={
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'draft': [('readonly', True)],
        'sent': [('readonly', True)],
        'to approve': [('readonly', True)],
        'cancel': [('readonly', True)],
    })

    @api.depends('contract_id.deadline_fulfilling_application_by_supplier')
    def _compute_date_planned(self):
        """ date_planned = the earliest date_planned across all order lines. """
        for order in self:
            try:
                delivery_schedule = order.contract_id.delivery_schedule_id.attendance_ids.mapped(
                    lambda x: int(x.dayofweek))
            except ValueError:
                order.date_planned = False
                break
            if delivery_schedule and isinstance(order.date_order, datetime):
                week_day = order.date_order.weekday()
                list_delta = map(lambda x: x - week_day, delivery_schedule)
                delta = min([x if x > 0 else x + 7 for x in list_delta])
                order.date_planned = order.date_order + timedelta(days=delta)
            else:
                order.date_planned = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        main_contract = self.env['account.analytic.account'].search([
            ('partner_id', '=', self.partner_id.id),
            ('is_main_contract', '=', True)
        ], limit=1)
        if main_contract:
            self.contract_id = main_contract.id
        else:
            self.contract_id = False

    def create(self, vals):
        rec = super(Purchase, self).create(vals)
        rec._onchange_partner_id()
        return rec


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        result = super(PurchaseOrderLine, self)._onchange_quantity()
        if not self.product_id:
            return
        if self.order_id.use_vendor_currency_rate:
            params = {'order_id': self.order_id}
            seller = self.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=self.order_id.date_order and self.order_id.date_order.date(),
                uom_id=self.product_uom,
                params=params)
            if seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
                price_unit = seller.price * self.order_id.vendor_rate
                self.price_unit = price_unit
        return result

    @api.model
    def create(self, values):
        rec = super(PurchaseOrderLine, self).create(values)
        rec._onchange_quantity()
        return rec
