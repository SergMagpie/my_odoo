from datetime import date
from odoo import fields, models, api


class ReplenishmentPolicies(models.Model):
    _name = 'stock.replenishment.policies'
    _description = 'Stock replenishment policies'
    _rec_name = 'name'

    name = fields.Char(
        string='Name replenishment police',
    )

    control_method = fields.Selection([
        ('manual', 'Manual control method'),
        ('automatic', 'Automatic control method'),
    ],
        default='manual',
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
    )

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
    )

    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product category',
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )

    begin_date = fields.Date(
        string='The date of the beginning',
    )

    end_date = fields.Date(
        string='Expiration date',
    )

    increase_trigger = fields.Float(
        digits=(16, 2),
        string='Increase trigger, %',
        help='At what penetration into the red zone will there be a recommendation to increase the buffer.'
    )

    increase_factor = fields.Float(
        digits=(16, 2),
        string='Increase factor, %',
        help='By how many% should the buffer be raised upon penetration into the red zone?',
    )

    decrease_trigger = fields.Float(
        digits=(16, 2),
        string='Decrease trigger, %',
        help='How many days the system accumulates the history of the remainder in the green zone of the buffer. Expressed in %, one day equals 100%',
    )

    decrease_factor = fields.Float(
        digits=(16, 2),
        string='Decrease factor, %',
        help='By how many% should the buffer be reduced when the remainder is in the green zone?',
    )

    action_history_ids = fields.One2many(
        comodel_name='replenishment.policies.action.history',
        inverse_name='policies_id',
        string='History of actions',
    )

    trigger_history_ids = fields.One2many(
        comodel_name='replenishment.policies.trigger.history',
        inverse_name='policies_id',
        string='History of triggers',
    )

    stock_warehouse_orderpoint_ids = fields.One2many(
        comodel_name='stock.warehouse.orderpoint',
        inverse_name='stock_replenishment_policies_id',
        string='Stock warehouse orderpoint',
        store=True,
    )

    orderpoints_count = fields.Integer(
        string='Orderpoints count',
        compute='compute_orderpoints_count',
        store=True,
    )

    sequence = fields.Integer(string='Sequence')

    is_actual = fields.Boolean(
        compute='compute_stock_warehouse_orderpoint_ids',
        store=True,
    )

    @api.depends('stock_warehouse_orderpoint_ids')
    def compute_orderpoints_count(self):
        for rec in self:
            rec.orderpoints_count = len(rec.stock_warehouse_orderpoint_ids)

    def action_view_orderpoints(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_orderpoint_replenish")
        action['domain'] = [('id', 'in', self.stock_warehouse_orderpoint_ids.ids)]
        return action

    @api.depends('warehouse_id', 'location_id', 'product_category_id', 'product_id', 'sequence', 'begin_date',
                 'end_date')
    def compute_stock_warehouse_orderpoint_ids(self):
        for rec in self:
            rec.is_actual = (rec.begin_date or date.today()
                             ) <= date.today() <= (rec.end_date or date.today())
            domain = rec.create_orderpoint_domain()
            stock_warehouse_orderpoints = rec.env['stock.warehouse.orderpoint'].search(domain)
            stock_warehouse_orderpoints.compute_stock_replenishment_policies_id()

    def create_orderpoint_domain(self):
        domain = [('is_buffer', '=', True)]
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))
        if self.location_id:
            domain.append(('location_id', '=', self.location_id.id))
        if self.product_category_id:
            domain.append(('product_category_id', '=', self.product_category_id.id))
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        return domain


class ReplenishmentPoliciesActionHistory(models.Model):
    _name = 'replenishment.policies.action.history'
    _description = 'Stock replenishment policies action history'

    policies_id = fields.Many2one(
        comodel_name='stock.replenishment.policies',
        string='Replenishment policies',
    )

    response_time = fields.Datetime(
        string='response time',
        default=fields.Datetime.now,
    )

    user_id = fields.Many2one(
        string='User',
        default=lambda self: self.env.user,
    )

    applied_action = fields.Selection([
        ('apply', 'Apply'),
        ('reject', 'Reject'),
    ],
        default=False,
    )

    buffer_zone = fields.Selection([
        ('is_green_zone', 'Is green zone'),
        ('is_red_zone', 'Is red zone'),
    ],
        default=False,
    )

    stock_warehouse_orderpoint_id = fields.Many2one(
        comodel_name='stock.warehouse.orderpoint',
        string='Stock warehouse orderpoint',
        store=True,
    )

class ReplenishmentPoliciesTriggerHistory(models.Model):
    _name = 'replenishment.policies.trigger.history'
    _description = 'Stock replenishment policies trigger history'

    policies_id = fields.Many2one(
        comodel_name='stock.replenishment.policies',
        string='Replenishment policies',
    )

    response_date = fields.Date(
        string='Response date',
        default=fields.Date.today,
    )

    buffer_zone = fields.Selection([
        ('is_green_zone', 'Is green zone'),
        ('is_red_zone', 'Is red zone'),
    ],
        default=False,
    )

    stock_warehouse_orderpoint_id = fields.Many2one(
        comodel_name='stock.warehouse.orderpoint',
        string='Stock warehouse orderpoint',
        store=True,
    )

    duration = fields.Integer(
        string='Duration',
        default=0,
        help='The difference in days from the moment the balance was detected in the green zone.',
    )