from odoo import models, fields


class HrResignation(models.Model):
    _inherit = 'hr.resignation'

    resignation_reason = fields.Many2one(
        comodel_name='resignation.reason.settings',
        string="Reason",
        required=True,
        help='Specify reason for leaving the company',
    )
