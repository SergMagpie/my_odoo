from odoo import fields, models, api


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    warehouse_manager_id = fields.Many2one(comodel_name='res.partner', string='Warehouse manager')
    contact_phone = fields.Char(string='Contact phone number')
