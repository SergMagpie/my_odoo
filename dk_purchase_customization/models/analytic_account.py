from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    contract_date_of_signing = fields.Date(
        string='Contract date of signing',
    )

    specification_price = fields.Selection(
        string='Specification price',
        selection=[
            ('specification', 'Specification'),
            ('price on the site', 'Price on the site'),
            ('price', 'Price'),
        ],
    )

    expiry_date_of_specification_price = fields.Date(
        string='Expiry date of specification price',
    )

    is_contract = fields.Boolean(
        string='This is a contract',
    )

    # contract_type = fields.Selection(
    #     string='Contract type',
    #     selection=[('customer', 'Customer'),
    #                ('supplier', 'Supplier'), ],
    # )

    full_name_custom = fields.Char(
        string='Full name',
    )

    non_resident = fields.Boolean(
        string='Non resident',
    )

    vat_certificate_number = fields.Char(
        string='Vat certificate number',
    )

    lending_limit_uan = fields.Float(
        string='Lending limit uan',
    )

    schedule_id = fields.Many2one(
        comodel_name='resource.calendar',
        string='Schedule',
    )

    order_schedule_id = fields.Many2one(
        comodel_name='resource.calendar',
        string='Order schedule',
    )
    delivery_schedule_id = fields.Many2one(
        comodel_name='resource.calendar',
        string='Delivery schedule',
    )
    deadline_fulfilling_application_by_supplier = fields.Integer(
        string='Deadline fulfilling application by supplier',
        help='Deadline for fulfilling the application by the supplier in days'
    )

    date_start = fields.Date(
        string='Date start',
    )

    date_end = fields.Date(
        string='Date end',
    )

    payment_terms_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Payment terms',
    )

    responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        default=lambda self: self.env.user.id,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )

    parent_contract_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Parent contract',
    )

    is_main_contract = fields.Boolean(
        string='Main contract',
        help='Is main contract'
    )
