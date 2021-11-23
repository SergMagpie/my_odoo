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

    user_position_id = fields.Many2one(
        comodel_name='hr.employee',
        compute='_compute_user_position_id',
        store=True,
    )

    @api.depends('user_id')
    def _compute_user_position_id(self):
        for order in self:
            order.user_position_id = order.env['hr.employee'].search([('user_id', '=', order.user_id.id)], limit=1)

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

    @api.model
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
        rec._get_tax_from_pricelist()
        rec._onchange_quantity()
        return rec

    def _get_tax_from_pricelist(self):
        for line in self:
            # todo: search 2 taxes without limit=1
            line._onchange_quantity()
            if line.seller_id and line.seller_id.product_supplier_info_vat_id:
                tax = self.env['account.tax'].search(
                    [('product_supplier_info_vat_id', '=', line.seller_id.product_supplier_info_vat_id.id),
                     ('type_tax_use', '=', 'purchase')], limit=1)
                line.update({'taxes_id': [(6, 0, tax.ids)]})
