# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    # @api.model
    # def _default_picking_type(self):
    #     data = self.project_id.get_project_stock_location_from_context()
    #     if not data:
    #         data = super(PurchaseRequest, self)._default_picking_type()
    #     return data

    construction_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        store=True,
    )

    # def _check_analytics_match(self):
    #     for item in self:
    #         for line in item.line_ids:
    #             if line.analytic_account_id.id not in line.relatives_account_analytic_ids.ids:
    #                 raise Warning(_('Analytic accounts in the order lines do not match the project name in the order!'))

    @api.model
    def create(self, vals):
        res = super(PurchaseRequest, self).create(vals)
        # res._check_analytics_match()
        return res

    def write(self, vals):
        res = super(PurchaseRequest, self).write(vals)
        # self._check_analytics_match()
        return res
