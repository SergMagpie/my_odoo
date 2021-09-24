# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    construction_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        store=True,
    )

    def action_create_invoice(self):
        action = super(PurchaseOrder, self).action_create_invoice()
        if action.get('res_id'):
            account_move = self.env['account.move'].browse(action['res_id'])
            account_move.update({
                'construction_project_id': self.construction_project_id.id,
            })
        return action

    def _prepare_picking(self):
        vals = super(PurchaseOrder, self)._prepare_picking()
        vals['construction_project_id'] = self.construction_project_id.id
        return vals


    # def _check_analytics_match(self):
    #     for rec in self:
    #         for line in rec.order_line:
    #             if line.account_analytic_id.id not in line.relatives_account_analytic_ids.ids:
    #                 raise Warning(_('Analytic accounts in the order lines do not match the project name in the order!'))

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        # res._check_analytics_match()
        return res

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        # self._check_analytics_match()
        return res
