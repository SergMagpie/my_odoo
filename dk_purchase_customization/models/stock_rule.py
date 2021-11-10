from odoo import fields, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id, origins, values)
        if res.get('date_order') < fields.Datetime.now():
            res['date_order'] = fields.Datetime.now()
        return res
