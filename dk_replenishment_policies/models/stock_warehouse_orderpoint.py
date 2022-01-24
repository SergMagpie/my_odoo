from datetime import datetime, time
from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    stock_replenishment_policies_id = fields.Many2one(
        comodel_name='stock.replenishment.policies',
        string='Stock replenishment policies',
        compute='compute_stock_replenishment_policies_id',
        store=True,
    )

    policies_trigger_history_ids = fields.One2many(
        comodel_name='replenishment.policies.trigger.history',
        inverse_name='stock_warehouse_orderpoint_id',
        string='Stock replenishment policies trigger history',
    )

    policies_action_history_ids = fields.One2many(
        comodel_name='replenishment.policies.action.history',
        inverse_name='stock_warehouse_orderpoint_id',
        string='Stock replenishment policies action history',
    )

    polices_control_method = fields.Selection(
        related='stock_replenishment_policies_id.control_method',
        readonly=True,
    )

    @api.depends('stock_replenishment_policies_id.warehouse_id',
                 'stock_replenishment_policies_id.location_id',
                 'stock_replenishment_policies_id.product_category_id',
                 'stock_replenishment_policies_id.product_id',
                 'stock_replenishment_policies_id.begin_date',
                 'stock_replenishment_policies_id.end_date',
                 'stock_replenishment_policies_id.sequence')
    def compute_stock_replenishment_policies_id(self):
        self.env['stock.replenishment.policies'].search([]).compute_is_actual()
        for rec in self:
            if rec.is_buffer:
                rec.stock_replenishment_policies_id = rec.get_replenishment_policies()
            else:
                rec.stock_replenishment_policies_id = False

    def get_replenishment_policies(self):
        domain = []
        if self.warehouse_id:
            domain.append(('warehouse_id', 'in', (self.warehouse_id.id, False)))
        if self.location_id:
            domain.append(('location_id', 'in', (self.location_id.id, False)))
        if self.product_category_id:
            domain.append(('product_category_id', 'in', (self.product_category_id.id, False)))
        if self.product_id:
            domain.append(('product_id', 'in', (self.product_id.id, False)))
        domain.append(('is_actual', '=', True))
        polices = self.env['stock.replenishment.policies'].search(domain, limit=1, order='sequence ASC, name ASC')
        return polices

    def cron_replenishment_policies(self):
        self.env['stock.replenishment.policies'].search([]).compute_is_actual()
        self.env["ir.logging"].sudo().create({
            "name": 'Start cron_replenishment_policies',
            "message": "",
            "type": "server",
            "path": "",
            "line": "",
            "func": ""
        })
        orderpoints_to_compute = self.search([('is_buffer', '=', True)])
        for orderpoint in orderpoints_to_compute:
            orderpoint.stock_replenishment_policies_id = orderpoint.get_replenishment_policies()
        orderpoints_with_policies = orderpoints_to_compute.filtered(
            lambda x: x.stock_replenishment_policies_id)
        orderpoints_with_policies._compute_zone()
        orderpoints_in_red_zone = orderpoints_with_policies.filtered(
            lambda x: x.is_red_zone
        )
        orderpoints_in_green_zone = orderpoints_with_policies.filtered(
            lambda x: x.is_green_zone
        )

        orderpoints_in_red_zone.update_history_replenishment_policies('is_red_zone')
        orderpoints_in_green_zone.update_history_replenishment_policies('is_green_zone')

        (orderpoints_in_red_zone + orderpoints_in_green_zone).compute_can_increase_decrease_buffer()

        orderpoints_for_increase_buffer = orderpoints_in_red_zone.filtered(
            lambda x: x.can_increase_buffer and x.stock_replenishment_policies_id.control_method == 'automatic'
        )
        self.env["ir.logging"].sudo().create({
            "name": 'Records to increase',
            "message": orderpoints_for_increase_buffer,
            "type": "server",
            "path": "",
            "line": "",
            "func": ""
        })
        for op in orderpoints_for_increase_buffer:
            op.increase_buffer_value()

        orderpoints_for_decrease_buffer = orderpoints_in_green_zone.filtered(
            lambda x: x.can_decrease_buffer and x.stock_replenishment_policies_id.control_method == 'automatic'
        )
        self.env["ir.logging"].sudo().create({
            "name": 'Records to decrease',
            "message": orderpoints_for_decrease_buffer,
            "type": "server",
            "path": "",
            "line": "",
            "func": "",
        })
        for op in orderpoints_for_decrease_buffer:
            op.decrease_buffer_value()

        orderpoints_without_zone = orderpoints_to_compute - orderpoints_in_red_zone - orderpoints_in_green_zone
        orderpoints_without_zone.policies_trigger_history_ids.unlink()
        self.env["ir.logging"].sudo().create({
            "name": 'END cron_replenishment_policies',
            "message": "",
            "type": "server",
            "path": "",
            "line": "",
            "func": ""
        })
        return True

    def update_history_replenishment_policies(self, zone):
        for rec in self:
            if rec.policies_trigger_history_ids and \
                    rec.policies_trigger_history_ids[0].policies_id == rec.stock_replenishment_policies_id and \
                    rec.policies_trigger_history_ids[0].buffer_zone == zone:
                if rec.policies_trigger_history_ids[0].response_date == fields.Date.today():
                    pass
                elif rec.policies_trigger_history_ids[0].buffer_zone == 'is_green_zone':
                    rec.policies_trigger_history_ids[0].duration += 1
                    rec.policies_trigger_history_ids[0].response_date = fields.Date.today()
            else:
                rec.policies_trigger_history_ids.unlink()
                rec.policies_trigger_history_ids.create({
                    'policies_id': rec.stock_replenishment_policies_id.id,
                    'response_date': fields.Date.today(),
                    'buffer_zone': zone,
                    'stock_warehouse_orderpoint_id': rec.id,
                    'duration': 0,
                })
        return True

    def compute_can_increase_decrease_buffer(self):
        self.compute_stock_replenishment_policies_id()
        for rec in self:
            if rec.stock_replenishment_policies_id:
                if rec.is_red_zone and rec.buffer_red_zone and (
                        rec.stock_replenishment_policies_id.increase_trigger < (
                        (rec.buffer_red_zone - rec.qty_on_hand) / rec.buffer_red_zone) * 100):
                    history_red_zones = rec.policies_action_history_ids.filtered(
                        lambda x: x.buffer_zone == 'is_red_zone' and x.applied_action != False)
                    last_action_time = history_red_zones.mapped(
                        'response_time')  # .filtered(lambda x: isinstance(x, datetime))
                    if last_action_time:
                        last_action_time = max(last_action_time)
                        difference_days_from_last_action = (datetime.now().date() - last_action_time.date()).days
                        waiting_time = rec.replenishment_time_days - difference_days_from_last_action
                    else:
                        waiting_time = -1
                    if waiting_time < 0:
                        rec.can_increase_buffer = True
                        rec.can_decrease_buffer = False
                    else:
                        rec.can_decrease_buffer = False
                        rec.can_increase_buffer = False
                elif rec.is_green_zone and \
                        (rec.stock_replenishment_policies_id.decrease_trigger < (
                                rec.policies_trigger_history_ids[
                                    0].duration * 100) if rec.policies_trigger_history_ids else True):
                    rec.can_decrease_buffer = True
                    rec.can_increase_buffer = False
                else:
                    rec.can_decrease_buffer = False
                    rec.can_increase_buffer = False
            else:
                super(StockWarehouseOrderpoint, rec).compute_can_increase_decrease_buffer()

    def increase_buffer_value(self):
        if self.stock_replenishment_policies_id:
            self.ensure_one()
            value_before = self.buffer_value
            self.buffer_value *= 1 + self.stock_replenishment_policies_id.increase_factor / 100
            self.write_policies_action_history(action='apply', buffer_zone='is_red_zone', value_before=value_before,
                                               value_after=self.buffer_value)
        else:
            super(StockWarehouseOrderpoint, self).increase_buffer_value()

    def decrease_buffer_value(self):
        if self.stock_replenishment_policies_id:
            self.ensure_one()
            value_before = self.buffer_value
            self.buffer_value *= 1 - self.stock_replenishment_policies_id.decrease_factor / 100
            self.write_policies_action_history(action='apply', buffer_zone='is_green_zone', value_before=value_before,
                                               value_after=self.buffer_value)
            self.update_history_replenishment_policies('is_green_zone')
            if self.policies_trigger_history_ids:
                self.policies_trigger_history_ids[0].duration = 0
        else:
            super(StockWarehouseOrderpoint, self).decrease_buffer_value()

    def reject_recommendations(self):
        self.ensure_one()
        if self.is_green_zone:
            self.write_policies_action_history(action='reject', buffer_zone='is_green_zone',
                                               value_before=self.buffer_value, value_after=self.buffer_value)
            self.update_history_replenishment_policies('is_green_zone')
            if self.policies_trigger_history_ids:
                self.policies_trigger_history_ids[0].duration = 0
            self.compute_can_increase_decrease_buffer()
        if self.is_red_zone:
            self.write_policies_action_history(action='reject', buffer_zone='is_red_zone',
                                               value_before=self.buffer_value, value_after=self.buffer_value)
            self.update_history_replenishment_policies('is_red_zone')
            self.compute_can_increase_decrease_buffer()

    def write_policies_action_history(self, action=False, buffer_zone=False, value_before=0.0, value_after=0.0):
        self.ensure_one()
        self.policies_action_history_ids.create({
            'policies_id': self.stock_replenishment_policies_id.id,
            'response_time': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'stock_warehouse_orderpoint_id': self.id,
            'applied_action': action,
            'buffer_zone': buffer_zone,
            'value_before': value_before,
            'value_after': value_after,
        })

    @api.depends('buffer_value')
    def compute_buffer_zone(self):
        rec = super(StockWarehouseOrderpoint, self).compute_buffer_zone()
        self.compute_can_increase_decrease_buffer()
        return rec
