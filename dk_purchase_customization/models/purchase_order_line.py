import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, api, _
# from odoo.exceptions import UserError


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
                    # product_secondary_unit.uom_id != line.product_uom,
                ]):
                    line.secondary_uom_id = product_secondary_unit
                    line.secondary_uom_qty = math.ceil(line.product_qty / product_secondary_unit.factor)
                    line.secondary_price = line.price_unit
                    line._onchange_secondary_price()
                    break
        return lines

    @api.model
    def _get_date_planned(self, seller, po=False):
        """ customization function for DK (compute delta from delivery schedule) """
        order = po if po else self.order_id
        date_order = order.date_order

        # compute delta from delivery schedule
        delivery_schedule = False
        try:
            delivery_schedule = order.contract_id.delivery_schedule_id.attendance_ids.mapped(
                lambda x: int(x.dayofweek))
        except ValueError:
            pass
            # raise UserError(
            #     _("Delivery schedule not defined or defined incorrectly"))
        if delivery_schedule and isinstance(date_order, datetime):
            week_day = date_order.weekday()
            list_delta = map(lambda x: x - week_day, delivery_schedule)
            delta = min([x if x > 0 else x + 7 for x in list_delta])
        else:
            delta = 0

        if date_order:
            date_planned = date_order + relativedelta(days=delta)
        else:
            date_planned = datetime.today() + relativedelta(days=delta)
        return self._convert_to_middle_of_day(date_planned)
