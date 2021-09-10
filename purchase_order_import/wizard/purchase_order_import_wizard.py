from io import BytesIO
from base64 import b64decode
import pandas as pd
from odoo import fields, models, api, _


class PurchaseOrderImportWizard(models.Model):
    _name = 'purchase.order.import.wizard'
    _description = 'PurchaseImport'

    import_file = fields.Binary(
        string="Import File",
        required=True
    )
    line_ids = fields.One2many(
        comodel_name='purchase.order.import.line.wizard',
        inverse_name='import_wizard_id',
        string='Lines'
    )
    line_count = fields.Integer(
        string='Line count',
        compute='_compute_line_count'
    )
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor'
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase order'
    )

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def parse_import_file(self):
        self.ensure_one()
        data_file = BytesIO(b64decode(self.import_file))
        df = pd.read_csv(data_file, header=None, skiprows=1, names=['barcode', 'default_code', 'name', 'qty', 'price'])
        for index, row in df.iterrows():
            po_product_barcode = self.env['product.barcode'].search([('name', '=', row['barcode'])], limit=1)

            default_code_product = False
            if row['default_code']:
                default_code_product = self.env['product.product'].search([('default_code', '=', row['default_code'])], limit=1)

            po_line = product_barcode_conflict = False
            if default_code_product and po_product_barcode:
                if po_product_barcode.product_id != default_code_product:
                    po_line = self.purchase_order_id.order_line.filtered(lambda l: l.product_id == default_code_product)  # conflict
                    product_barcode_conflict = True
                else:
                    po_line = self.purchase_order_id.order_line.filtered(lambda l: l.product_id == po_product_barcode.product_id)
            elif default_code_product:
                po_line = self.purchase_order_id.order_line.filtered(lambda l: l.product_id == default_code_product)
            elif po_product_barcode:
                po_line = self.purchase_order_id.order_line.filtered(lambda l: l.product_id == po_product_barcode.product_id)

            if po_line:
                po_line = po_line[0]
                line_wizard = self.env['purchase.order.import.line.wizard'].create({
                    'product_id': po_line.product_id.id,
                    'barcode': row['barcode'],
                    'qty': row['qty'],
                    'price': row['price'],
                    'purchase_order_line_id': po_line.id,
                    'import_wizard_id': self.id,
                    'product_barcode_conflict': product_barcode_conflict,
                })

        return {
            'name': _('Import Purchase Order Lines'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.import.wizard',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new'
        }

    def update_purchase(self):
        for line in self.line_ids:
            line.purchase_order_line_id.update({
                'barcode': line.barcode,
                'product_qty': line.qty,
                'price_unit': line.price,
                'product_barcode_conflict': line.product_barcode_conflict,
            })

    def update_purchase_and_create_vendor_bill(self):
        self.update_purchase()
        purchase_order = self.purchase_order_id
        vals = {
            'partner_id': purchase_order.partner_id.id,
            'move_type': 'in_invoice',
            'purchase_id': purchase_order.id,
            'invoice_origin': purchase_order.name,
            'invoice_line_ids': [],
        }
        for line in self.line_ids:
            purchase_order_line = line.purchase_order_line_id
            vals['invoice_line_ids'].append((0, 0, {
                'name': purchase_order_line.name,
                'product_id': purchase_order_line.product_id.id,
                'quantity': purchase_order_line.product_qty,
                'price_unit': purchase_order_line.price_unit,
                'product_uom_id': purchase_order_line.product_uom.id,
                'purchase_line_id': purchase_order_line.id,
            }))

        new_vals = self.env['account.move']._move_autocomplete_invoice_lines_create([vals])
        invoice = self.env['account.move'].create(new_vals)
        return purchase_order.action_view_invoice()


class PurchaseOrderImportLineWizard(models.Model):
    _name = 'purchase.order.import.line.wizard'
    _description = 'Purchase Order Import Line Wizard'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    barcode = fields.Char(
        string='Barcode',
    )
    qty = fields.Float(
        string='Qty')
    price = fields.Float(
        string='Price')
    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase order line')
    import_wizard_id = fields.Many2one(
        comodel_name='purchase.order.import.wizard',
        string='Import wizard'
    )
    product_barcode_conflict = fields.Boolean(
        string='Product barcode conflict',
        default=False
    )
