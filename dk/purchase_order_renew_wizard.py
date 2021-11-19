from io import BytesIO
from base64 import b64decode
import pandas as pd
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


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
        df = pd.read_excel(data_file, sheet_name=0, index_col=None, header=None)
        po_name = df.loc[0:0].values[0][1]
        height, width = df.shape
        if self.purchase_order_id.name != po_name:
            raise ValidationError(_("The loaded file does not match the order name!"))
        elif width != 7 or height - 7 != len(self.purchase_order_id.order_line):
            raise ValidationError(_("The loaded file does not match the file structure!"))
        else:
            lines = df.loc[6:height - 2].values
            for line in lines:
                line_number = line[0]
                vendor_code = line[1]
                if not vendor_code:
                    raise ValidationError(
                        _("The loaded file does not match the vendor code in the line number %s!") % line_number)
                purchase_order_line = self.purchase_order_id.order_line.search(
                    [('order_id', '=', self.purchase_order_id.id), ('seller_id.vendor_code', '=', vendor_code)],
                    limit=1)
                if not purchase_order_line:
                    raise ValidationError(
                        _("The vendor code does not match with purchase order in the line number %s!") % line_number)
                else:
                    line_wizard = self.env['purchase.order.import.line.wizard'].create({
                        'line_number': line_number,
                        'vendor_code': vendor_code,
                        'product_name': line[2],
                        'secondary_uom_qty': line[3],
                        'secondary_uom_id': purchase_order_line.secondary_uom_id.id,
                        'secondary_price': line[5],
                        'price_total': line[6],
                        'purchase_order_line_id': purchase_order_line.id,
                        'import_wizard_id': self.id,
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
        for purchase_order_line_id in self.purchase_order_id.order_line:
            purchase_order_line_id.update({
                'qty_received': self.line_ids.search([('import_wizard_id', '=', self.id),
                                                      ('purchase_order_line_id', '=', purchase_order_line_id.id)],
                                                     limit=1).secondary_uom_qty or 0
            })


class PurchaseOrderImportLineWizard(models.Model):
    _name = 'purchase.order.import.line.wizard'
    _description = 'Purchase Order Import Line Wizard'

    line_number = fields.Integer(
        string='Line number'
    )

    vendor_code = fields.Char(
        string='Vendor Code'
    )

    product_name = fields.Char(
        string='Supplier\'s product name')

    secondary_uom_qty = fields.Float(
        string='Secondary Qty'
    )

    secondary_uom_id = fields.Many2one(
        comodel_name="product.secondary.unit",
        string="Secondary uom",
        ondelete="restrict",
    )

    secondary_price = fields.Float(string='Price with VAT')

    price_total = fields.Float(string='Value with VAT')

    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase order line')

    import_wizard_id = fields.Many2one(
        comodel_name='purchase.order.import.wizard',
        string='Import wizard'
    )
