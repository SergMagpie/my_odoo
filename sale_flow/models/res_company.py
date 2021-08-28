# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_order_custom_report_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Sale Order Custom Report',
        domain=[('type', '=', 'qweb')]
    )
    option_markup_first = fields.Float(
        string='Option markup first'
    )
    option_markup_second = fields.Float(
        string='Option markup second'
    )
    option_markup_third = fields.Float(
        string='Option markup third'
    )

    # Watermark properties
    add_watermark = fields.Boolean(
        string='Use Watermark?',
        default=False,
        help="Check if you want to add a Watermark to your reports."
    )
    watermark_selection = fields.Selection(
        [('letter_head', 'Letter Head'),
         ('company_logo', 'Company Logo'),
         ('custom_name', 'Text'),
         ('time', 'Date')],
        string='Watermark Selection'
    )
    custom_watermark_name = fields.Char(
        string='Watermark Name'
    )
    letter_head = fields.Binary(
        string='Letter Head'
    )
    time = fields.Datetime(
        string='Time'
    )
