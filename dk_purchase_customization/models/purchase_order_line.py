import math

from odoo import models, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            for product_secondary_unit in line.product_id.secondary_uom_ids:
                if all([
                    product_secondary_unit.vendor_id == line.partner_id,
                    product_secondary_unit.factor,
                    product_secondary_unit.uom_id != line.product_uom,
                ]):
                    line.secondary_uom_id = product_secondary_unit
                    line.secondary_uom_qty = math.ceil(line.product_qty / product_secondary_unit.factor)
                    line.secondary_price = line.price_unit
                    line._onchange_secondary_price()
        return lines
