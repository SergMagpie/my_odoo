from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    construction_project_id = fields.Many2one(
        related='order_id.construction_project_id',
        string='Project',
        readonly=True,
        store=True,
    )

    relatives_account_analytic_ids = fields.Many2many(
        comodel_name='account.analytic.account',
        string='Relatives account analytic',
        compute='_compute_relatives_account_analytic_ids',
    )

    @api.depends('product_id', 'date_order')
    def _compute_analytic_id_and_tag_ids(self):
        result = super(PurchaseOrderLine, self)._compute_analytic_id_and_tag_ids()
        for rec in self:
            if rec.construction_project_id.analytic_account_id:
                rec.account_analytic_id = rec.construction_project_id.analytic_account_id
        return result

    @api.depends('construction_project_id')
    def _compute_relatives_account_analytic_ids(self):
        for rec in self:
            record_analytic_id = rec.construction_project_id.analytic_account_id
            while record_analytic_id.parent_id:
                record_analytic_id = record_analytic_id.parent_id
            account_analytic_ids = rec.env['account.analytic.account'].search(
                [('id', 'child_of', record_analytic_id.id)]).ids
            rec.relatives_account_analytic_ids = [(6, 0, account_analytic_ids)]
