from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def purchase_order_import_wizard_action(self):
        return {
            'name': _('Import Purchase Order Lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.import.wizard',
            'type': 'ir.actions.act_window',
            'context': {'default_vendor_id': self.partner_id.id,
                        'default_purchase_order_id': self.id},
            'target': 'new'
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    barcode = fields.Char(
        string='Barcode',
        required=False)
    product_barcode_conflict = fields.Boolean(
        string='Product barcode conflict',
        default=False)
    production_date = fields.Integer(
        string='Production date',
    )

    def update_barcode(self):
        for order_line in self:
            barcode = self.env['ir.sequence'].next_by_code('product.barcode')
            self.env['product.barcode'].create({
                'name': barcode,
                'product_id': order_line.product_id.id,
            })
            order_line.update({
                'barcode': barcode,
                'product_barcode_conflict': False,
            })
