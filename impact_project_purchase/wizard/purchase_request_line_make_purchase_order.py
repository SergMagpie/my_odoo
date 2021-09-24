from odoo import fields, models, api


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    construction_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model", False)
        if active_model == "purchase.request":
            request_ids = self.env.context.get("active_id", False)
            purchase_request = self.env[active_model].browse(request_ids)
            res['construction_project_id'] = purchase_request.construction_project_id.id
        return res

    @api.model
    def _prepare_purchase_order(self, *args):
        data = super(PurchaseRequestLineMakePurchaseOrder, self)._prepare_purchase_order(*args)
        data['construction_project_id'] = self.construction_project_id.id
        return data
