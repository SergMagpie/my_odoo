# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging  #Get the logger

_logger = logging.getLogger(__name__) #Get the logger


class AnalogueCatalogue(models.Model):
    _name = 'analogue.catalogue'

    name = fields.Char(string=_('Code of Analogue'), required=True)
    analogue_brand = fields.Many2one('res.partner',
                                     string='Brand of Analogue',
                                     required=True)
    internal_notes = fields.Text(string=_("Seller's notes"))
    product_id = fields.Many2one('product.product', string=_('RKB Product'))
    product_templ_id = fields.Many2one(related='product_id.product_tmpl_id', string=_('RKB Product Template'))

    @api.model
    def create(self, vals):
        New_id = super(AnalogueCatalogue, self).create(vals)
        if not New_id.product_id:
            zero_product = self.env['ir.model.data'].get_object('sale_flow', 'product_product_0').id
            New_id.product_id = zero_product
        return New_id
