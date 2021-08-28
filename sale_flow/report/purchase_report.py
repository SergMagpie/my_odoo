# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    state = fields.Selection([
        ('draft', 'Draft RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('received', 'RFQ Received'),
        ('so_updated', 'SO Updated'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], 'Order Status', readonly=True)
