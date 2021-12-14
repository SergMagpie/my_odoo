from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, values):
        rec = super(SaleOrder, self).create(values)
        rec.calculate_and_update_europe_quantities()
        return rec

    def calculate_and_update_europe_quantities(self):
        """
        Алгоритм присвоения срока поставки:
        Если в колонке Quantity CH, есть необходимое кол-во - срок поставки указывается 2-4 недели (по согласованию).
        Если в колонке Quantity CH, нет необходимого кол-ва, проверить колонку Quantity MI. Если кол-ва хватает из обеих колонок - срок поставки указывается 2-4 недели (по согласованию).
        Если в колонке Quantity CH и колонке Quantity MI нет необходимого кол-ва, проверить колонки Quantity RHO/ Quantity EE - срок поставки указывается 6- 8 недель (по согласованию).

        Если часть необходимого кол-ва есть в Quantity CH/Quantity MI, а часть в Quantity RHO/ Quantity EE - срок поставки в КП должен быть указан соответственно (например, общее кол-во 10, 5 шт есть в Quantity CH/Quantity MI, а 5 шт есть в Quantity RHO/ Quantity EE, срок поставки будет 5шт 2-4 недели (по согласованию) и 5 шт 6- 8 недель (по согласованию).
        """
        params = self.env['ir.config_parameter'].sudo()
        planned_date_switzerland = int(params.get_param('product_quantities_update.planned_date_switzerland')) or False
        planned_date_italy = int(params.get_param('product_quantities_update.planned_date_italy')) or False
        planned_date_romania = int(params.get_param('product_quantities_update.planned_date_romania')) or False
        for order_line in self.order_line:
            order_line.product_id.get_europe_quantities()
            need_quantity = order_line.product_uom_qty
            product = order_line.product_id
            if not (product.quantity_Switzerland or product.quantity_Italy or product.quantity_Romania):
                continue

            flag = False
            if 0 < need_quantity <= product.quantity_Switzerland:
                order_line.rkb_date_planned = planned_date_switzerland
                flag = True
            elif 0 < need_quantity <= product.quantity_Italy:
                order_line.rkb_date_planned = planned_date_italy
                flag = True
            elif 0 < need_quantity <= product.quantity_Italy + product.quantity_Switzerland:  # strange
                order_line.rkb_date_planned = planned_date_italy
                flag = True
            elif 0 < need_quantity <= product.quantity_Romania:
                order_line.rkb_date_planned = planned_date_romania
                flag = True

            if not flag:

                if 0 < product.quantity_Switzerland:
                    order_line.product_uom_qty = min((need_quantity, product.quantity_Switzerland))
                    order_line.rkb_date_planned = planned_date_switzerland
                    need_quantity = max((0, need_quantity - product.quantity_Switzerland))

                    if need_quantity > 0:
                        order_line = order_line.copy({'order_id': self.id})

                if 0 < product.quantity_Italy:
                    order_line.product_uom_qty = min((need_quantity, product.quantity_Italy))
                    order_line.rkb_date_planned = planned_date_italy
                    need_quantity = max((0, need_quantity - product.quantity_Italy))

                    if need_quantity > 0:
                        order_line = order_line.copy({'order_id': self.id})

                if 0 < product.quantity_Romania:
                    order_line.product_uom_qty = min((need_quantity, product.quantity_Romania))
                    order_line.rkb_date_planned = planned_date_romania
                    need_quantity = max((0, need_quantity - product.quantity_Romania))

                    if need_quantity > 0:
                        order_line = order_line.copy({'order_id': self.id})

                if need_quantity > 0:
                    order_line.rkb_date_planned = False
                    order_line.product_uom_qty = need_quantity

