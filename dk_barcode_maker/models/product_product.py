# from odoo import fields, models, api
#
#
# class Product(models.Model):
#     _name = "product.product"
#     _inherit = ['product.product', 'dk.barcode.maker']
#
#
#     barcode_image = fields.Binary(
#         string="Barcode image",
#         compute="_compute_barcode_image",
#     )
#
#     @api.depends('barcode')
#     def _compute_barcode_image(self):
#         for record in self:
#             record.barcode_image = record.create_barcode(record.barcode)