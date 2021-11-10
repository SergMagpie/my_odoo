from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductSecondaryUnit(models.Model):
    _inherit = "product.secondary.unit"

    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
    )

    @api.constrains('vendor_id', 'product_tmpl_id')
    def _validate_secondary_unit(self):
        for record in self:
            if self.env['product.secondary.unit'].search_count(
                    [
                        ('product_tmpl_id', '=', record.product_tmpl_id.id),
                        ('vendor_id', '=', record.vendor_id.id)
                    ]) > 1:
                raise ValidationError(_("A product can only have one unit of measure from one supplier!"))
