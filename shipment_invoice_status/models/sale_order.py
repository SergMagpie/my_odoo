from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_shipment_status(self):
        for rec in self:
            if rec.picking_ids and all(picking.state != 'draft' for picking in rec.picking_ids):
                if any(picking.state == 'done' for picking in rec.picking_ids):
                    if all(picking.state == 'done' for picking in rec.picking_ids):
                        rec.shipment_status_so = 'shipped_completely'
                    else:
                        rec.shipment_status_so = 'partially_shipped'
                else:
                    rec.shipment_status_so = 'not_shipped'

    def get_invoice_status(self):
        for rec in self:
            if rec.invoice_ids and all(picking.state != 'draft' for picking in rec.picking_ids):
                if any(inv.state == 'paid' for inv in rec.invoice_ids) or any(
                        payment.state == 'posted' and payment.amount > 0 for payment in
                        rec.invoice_ids.mapped('payment_ids')):
                    if all(inv.state == 'paid' for inv in rec.invoice_ids):
                        rec.invoice_status_so = 'paid'
                    else:
                        rec.invoice_status_so = 'partially_paid'
                else:
                    rec.invoice_status_so = 'not_paid'

    shipment_status_so = fields.Selection([('not_shipped', _('Not Shipped')),
                                           ('partially_shipped', _('Partially shipped')),
                                           ('shipped_completely', _('Shipped completely'))],
                                          string='Shipment Status',
                                          compute='get_shipment_status',
                                          search='_search_shipment_status_so')

    invoice_status_so = fields.Selection([('not_paid', _('Not Paid')),
                                          ('partially_paid', _('Partially paid')),
                                          ('paid', _('Paid'))],
                                         string='Invoice status',
                                         compute='get_invoice_status',
                                         search='_search_invoice_status_so')

    def _search_shipment_status_so(self, operator, value):
        if operator == '=' and value:
            orders = self.search([]).filtered(lambda x: x.shipment_status_so == value)
            if orders:
                return [('id', 'in', [order.id for order in orders])]
            else:
                return [('id', 'in', [0])]
        else:
            raise UserError(_('This search is not supported for this field, sorry!'))

    def _search_invoice_status_so(self, operator, value):
        if operator == '=' and value:
            orders = self.search([]).filtered(lambda x: x.invoice_status_so == value)
            if orders:
                return [('id', 'in', [order.id for order in orders])]
            else:
                return [('id', 'in', [0])]
        else:
            raise UserError(_('This search is not supported for this field, sorry!'))
