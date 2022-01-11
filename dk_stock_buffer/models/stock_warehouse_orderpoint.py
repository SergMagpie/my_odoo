from datetime import datetime
from odoo import models, fields, api, _
from odoo.tools import float_compare, float_round
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class StockWarehouseOrderpoint(models.Model):
    _name = 'stock.warehouse.orderpoint'
    _inherit = ["mail.thread", "mail.activity.mixin", "stock.warehouse.orderpoint"]

    is_buffer = fields.Boolean(
        string='Buffer'
    )
    buffer_value = fields.Float(
        string='Start value',
        digits=(16, 3),
    )
    buffer_yellow_zone = fields.Float(
        string='Yellow zone',
        digits=(16, 3),
        compute='compute_buffer_zone',
        store=True
    )
    buffer_red_zone = fields.Float(
        string='Red zone',
        digits=(16, 3),
        compute='compute_buffer_zone',
        store=True
    )
    buffer_critical_zone = fields.Float(
        string='Critical zone',
        digits=(16, 3),
        compute='compute_buffer_zone',
        store=True
    )
    buffer_change_date = fields.Datetime(
        string='Buffer change date',
        compute='compute_buffer_zone',
        store=True
    )
    critical_zone_period = fields.Float(
        string='Critical zone period'
    )
    green_zone_period = fields.Float(
        string='Green zone period'
    )
    can_increase_buffer = fields.Boolean(
        # compute='compute_can_increase_buffer',
        store=True,
    )
    can_decrease_buffer = fields.Boolean(
        # compute='compute_can_decrease_buffer',
        store=True,
    )
    product_min_qty = fields.Float(
        digits=(16, 3),
    )
    product_max_qty = fields.Float(
        digits=(16, 3),
    )
    qty_forecast = fields.Float(
        store=False,
    )
    qty_to_order = fields.Float(
        store=True,
    )

    is_red_zone = fields.Boolean(
        store=True,
        compute='_compute_zone',
    )

    is_yellow_zone = fields.Boolean(
        store=True,
        compute='_compute_zone',
    )

    is_green_zone = fields.Boolean(
        store=True,
        compute='_compute_zone',
    )
    replenishment_time_days = fields.Integer(
        string='Replenishment time (days)',
        compute='_compute_replenishment_time_days',
        help="""Mapping:
Кол-во заказов в неделю у поставщика	| Время пополнения
1	| 10
2	| 6
3	| 4
4	| 3
5	| 3

Кол-во заказов в неделю у поставщика с контракта
""",
        store=False,
    )

    def _compute_replenishment_time_days(self):
        schedule_day_to_replenishment_day_mapping = {
            1: 10,
            2: 6,
            3: 4,
            4: 3,
            5: 3,
        }
        for rec in self:
            replenishment_time_days = 0
            seller = rec.product_id.seller_ids.sorted('sequence')[:1]
            if seller:
                vendor = seller[0].name

                contract = self.env['account.analytic.account'].search([('is_contract', '=', True),
                                                                        ('is_main_contract', '=', True),
                                                                        ('partner_id', '=', vendor.id),
                                                                        ('contract_type', '=', 'purchase'), ], limit=1)
                replenishment_time_days = contract.order_schedule_id.number_of_days

            rec.replenishment_time_days = schedule_day_to_replenishment_day_mapping.get(replenishment_time_days, 0)

    @api.model
    def fields_view_get(self, *args, **kwargs):
        # todo do something with this crutch
        if 'tree' in args:
            self.search([('is_buffer', '=', True)]).compute_can_increase_decrease_buffer()
        return super(StockWarehouseOrderpoint, self).fields_view_get(*args, **kwargs)

    def _compute_qty(self):
        res = super(StockWarehouseOrderpoint, self)._compute_qty()
        self._compute_qty_to_order()
        self._compute_zone()
        return res

    @api.depends('buffer_yellow_zone', 'buffer_red_zone', 'qty_on_hand', 'buffer_value', 'is_buffer')
    def _compute_zone(self):
        for rec in self:
            rec.is_red_zone = 0 < rec.qty_on_hand <= rec.buffer_red_zone and rec.is_buffer
            rec.is_yellow_zone = rec.buffer_yellow_zone >= rec.qty_on_hand > rec.buffer_red_zone and rec.is_buffer
            rec.is_green_zone = rec.buffer_value >= rec.qty_on_hand > rec.buffer_yellow_zone and rec.is_buffer

    @api.depends('buffer_value')
    def compute_buffer_zone(self):
        for rec in self:
            rec.buffer_yellow_zone = float_round(0.67 * rec.buffer_value, precision_rounding=rec.product_uom.rounding or 1)
            rec.buffer_red_zone = float_round(0.33 * rec.buffer_value, precision_rounding=rec.product_uom.rounding or 1)
            rec.buffer_critical_zone = float_round(0.165 * rec.buffer_value, precision_rounding=rec.product_uom.rounding or 1)
            rec.buffer_change_date = datetime.now()
        self._compute_zone()

    @api.depends('qty_multiple', 'qty_forecast', 'product_min_qty', 'product_max_qty', 'buffer_value', 'is_buffer')
    def _compute_qty_to_order(self):
        for orderpoint in self:
            if orderpoint.is_buffer:
                qty_to_order = orderpoint.buffer_value - orderpoint.qty_forecast

                remainder = orderpoint.qty_multiple > 0 and qty_to_order % orderpoint.qty_multiple or 0.0
                if float_compare(remainder, 0.0, precision_rounding=orderpoint.product_uom.rounding) > 0:
                    qty_to_order += orderpoint.qty_multiple - remainder
                orderpoint.qty_to_order = qty_to_order if qty_to_order > 0 else 0
            else:
                if not orderpoint.product_id or not orderpoint.location_id:
                    orderpoint.qty_to_order = False
                    continue
                qty_to_order = 0.0
                rounding = orderpoint.product_uom.rounding
                if float_compare(orderpoint.qty_forecast, orderpoint.product_min_qty, precision_rounding=rounding) < 0:
                    qty_to_order = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - orderpoint.qty_forecast

                    remainder = orderpoint.qty_multiple > 0 and qty_to_order % orderpoint.qty_multiple or 0.0
                    if float_compare(remainder, 0.0, precision_rounding=rounding) > 0:
                        qty_to_order += orderpoint.qty_multiple - remainder
                orderpoint.qty_to_order = qty_to_order

    def cron_make_orderpoint_activity(self):
        orderpoint_to_order = self.search([('qty_to_order', '>', 0.0)])
        for orderpoint in orderpoint_to_order:
            # TODO make sorting more optimized
            supplier = orderpoint.product_id.seller_ids.sorted(key=lambda act: (act.active_supplier, act.sequence))[-1:]
            if supplier:
                contract = self.env['account.analytic.account'].search(
                    [('partner_id', '=', supplier.name.id), ('is_contract', '=', True)])
                if contract and contract.order_schedule_id:
                    next_date = self.get_next_date(contract.order_schedule_id)
                    self.env['mail.activity'].create({
                        'date_deadline': next_date,
                        'summary': 'Need to supply',
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'res_model_id': self.env.ref('stock.model_stock_warehouse_orderpoint').id,
                        'res_id': orderpoint.id,
                    })

    def get_next_date(self, schedule):
        date_number = fields.date.today().weekday()
        result_dayofweek = int(schedule.attendance_ids.mapped('dayofweek')[0])
        for dayofweek in schedule.attendance_ids.mapped('dayofweek'):
            if int(dayofweek) >= date_number:
                result_dayofweek = int(dayofweek)
                break
        return fields.date.today() + relativedelta(weekday=result_dayofweek)

    def increase_buffer_value(self):
        self.ensure_one()
        self.buffer_value *= 1.33
        self.compute_can_increase_decrease_buffer()

    def decrease_buffer_value(self):
        self.ensure_one()
        self.buffer_value *= 0.67
        self.compute_can_increase_decrease_buffer()

    # def compute_can_increase_buffer(self):
    #     red_zone_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.critical_zone_period', 1))
    #     buffer_change_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.buffer_change_period', 1))
    #     for rec in self:
    #         buffer_change_delta = (fields.datetime.now() - rec.buffer_change_date).seconds / 3600
    #         if rec.qty_on_hand <= rec.buffer_critical_zone and buffer_change_delta >= buffer_change_period and rec.critical_zone_period >= red_zone_period:
    #             rec.can_increase_buffer = True
    #         else:
    #             rec.can_increase_buffer = False
    #
    # def compute_can_decrease_buffer(self):
    #     green_zone_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.green_zone_period', 1))
    #     buffer_change_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.buffer_change_period', 1))
    #     for rec in self:
    #         buffer_change_delta = (fields.datetime.now() - rec.buffer_change_date).seconds / 3600
    #         if rec.buffer_value >= rec.qty_on_hand >= rec.buffer_yellow_zone and buffer_change_delta >= buffer_change_period and rec.green_zone_period >= green_zone_period:
    #             rec.can_decrease_buffer = True
    #         else:
    #             rec.can_decrease_buffer = False

    def compute_can_increase_decrease_buffer(self):
        red_zone_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.critical_zone_period', 1))
        green_zone_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.green_zone_period', 1))
        buffer_change_period = float(self.env['ir.config_parameter'].sudo().get_param('stock.buffer_change_period', 1))
        for rec in self:
            buffer_change_delta = (datetime.now() - rec.buffer_change_date).seconds / 3600
            if rec.qty_on_hand <= rec.buffer_critical_zone and buffer_change_delta >= buffer_change_period and rec.critical_zone_period >= red_zone_period:
                rec.can_increase_buffer = True
                rec.can_decrease_buffer = False
            elif rec.buffer_value >= rec.qty_on_hand >= rec.buffer_yellow_zone and buffer_change_delta >= buffer_change_period and rec.green_zone_period >= green_zone_period:
                rec.can_decrease_buffer = True
                rec.can_increase_buffer = False
            else:
                rec.can_decrease_buffer = False
                rec.can_increase_buffer = False

    def cron_update_zone_period(self):
        for orderpoint in self.search([]):
            # process green zone
            if orderpoint.qty_on_hand > orderpoint.buffer_yellow_zone:
                orderpoint.write({
                    'critical_zone_period': 0.0,
                    'green_zone_period': orderpoint.green_zone_period + 24
                })
            # process critical zone
            elif orderpoint.qty_on_hand < orderpoint.buffer_critical_zone:
                orderpoint.write({
                    'critical_zone_period': orderpoint.critical_zone_period + 24,
                    'green_zone_period': 0.0
                })
            # reset if not in zone
            else:
                orderpoint.write({
                    'critical_zone_period': 0.0,
                    'green_zone_period': 0.0
                })

    def cron_update_buffer_value(self):
        # TODO filter orderpoint by buffer_change_date
        for orderpoint in self.search([]):
            if orderpoint.can_increase_buffer:
                orderpoint.increase_buffer_value()
            elif orderpoint.can_decrease_buffer:
                orderpoint.decrease_buffer_value()

    @api.constrains('product_id', 'warehouse_id')
    def _check_duplicates(self):
        for rec in self:
            if self.env['stock.warehouse.orderpoint'].search_count([
                ('product_id', '=', rec.product_id.id),
                ('warehouse_id', '=', rec.warehouse_id.id),
            ]) > 1:
                raise UserError(
                    _("An error occurred while creating a replenishment rule, a replenishment rule for the specified product already exists at the specified storage location."))

    def action_set_triggers_manual_auto(self, setter='auto'):
        return self.write({'trigger': setter})
