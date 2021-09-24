# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request.line'

    construction_project_id = fields.Many2one(
        related='request_id.construction_project_id',
        string='Project',
        readonly=True,
        store=True,
    )

    relatives_account_analytic_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        string='Relatives account analytic',
        compute='_compute_relatives_account_analytic_ids',
    )

    @api.depends('construction_project_id')
    def _compute_relatives_account_analytic_ids(self):
        for rec in self:
            record_analytic_id = rec.construction_project_id.analytic_account_id
            while record_analytic_id.parent_id:
                record_analytic_id = record_analytic_id.parent_id
            account_analytic_ids = rec.env['account.analytic.account'].search(
                [('id', 'child_of', record_analytic_id.id)]).ids
            rec.relatives_account_analytic_ids = [(6, 0, account_analytic_ids)]

    @api.onchange('product_id')
    def _compute_analytic_id_and_tag_ids(self):
        for rec in self:
            if rec.construction_project_id.analytic_account_id:
                rec.analytic_account_id = rec.construction_project_id.analytic_account_id
