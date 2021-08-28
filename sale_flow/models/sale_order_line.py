# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    option_price_first = fields.Float(
        related='product_id.option_price_first'
    )
    option_price_second = fields.Float(
        related='product_id.option_price_second'
    )
    option_price_third = fields.Float(
        related='product_id.option_price_third'
    )

    def set_option_price(self):
        self.ensure_one()
        field_to_set = self._context.get('set_price', False)
        if field_to_set:
            self.price_unit = getattr(self, field_to_set)
        return True

    def reset_price_unit(self):
        self.ensure_one()
        self.price_unit = False
        return True

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        self.price_unit = self.product_id.option_price_first
        return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        self.price_unit = self.product_id.option_price_first
        return res

    def search_product_with_similar_suffix(self):
        product_name = self.name
        suffix_product = re.findall(r'\d+', product_name)[-1]
        view_id_tree = self.env.ref('sale_flow.analog_product_tree_view')
        action = {
            'name': _('list with similar suffixes'),
            'view_mode': 'tree,kanban,form',
            'res_model': 'product.product',
            'views': [(view_id_tree.id, 'tree'), (False, 'kanban'), (False, 'form')],
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [
                ('name', 'like', suffix_product),
            ],
        }
        return action

    class Product(models.Model):
        _inherit = "product.product"

        qty_available = fields.Float(
            store=True,
        )
