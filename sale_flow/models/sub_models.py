# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CustomerActivity(models.Model):
    _name = 'rkb.customer.activity'
    _rec_name = 'name'

    name = fields.Char('Status/Customer activity')


class DepartmentCustomerExecutive(models.Model):
    _name = 'rkb.department.customer.executive'
    _rec_name = 'name'

    name = fields.Char("Department of Customer's executive")

class LeadAimCustomerQuotation(models.Model):
    _name = 'rkb.lead.customer.aim'
    _description = 'Customer aim'

    name = fields.Char('Aim', required=True)


class ProductItemType(models.Model):
    _name = 'rkb.product.item.type'
    _description = 'Item type'

    name = fields.Char('Item Type', required=True)
    duty = fields.Float('Duty')
    code = fields.Char('Code')
    rkb_categ_analog_ids = fields.One2many('rkb.product.item.type.analog', 'rkb_categ_id', string='RKB Categ Analog')

class ProductItemTypeAnalog(models.Model):
    _name = 'rkb.product.item.type.analog'
    _description = 'Item type analog'

    name = fields.Char('Item Type Analog', required=True)
    rkb_categ_id = fields.Many2one('rkb.product.item.type', string='RKB Categ')


class RkbPlanedDate(models.Model):
    _name = 'rkb.planed.date'
    _rec_name = 'name'

    name = fields.Char('Planed Date', required=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    invoice_number = fields.Char('Invoice #')
    contract_specification = fields.Char('Contract/Specification')
    total_net_weight = fields.Char('Total net weight/kg')
    total_gross_weight = fields.Char('Total gross weight/kg')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    driver_id = fields.Many2one('res.partner', string='Driver')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')


class DeliveryCondition(models.Model):
    _name = 'rkb.delivery.condition'
    _rec_name = 'name'

    name = fields.Char('Delivery Condition')


class DeliveryType(models.Model):
    _name = 'rkb.delivery.type'
    _rec_name = 'name'

    name = fields.Char('Delivery Type', required=True)
