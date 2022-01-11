from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    green_zone_period = fields.Float(
        string='Green zone period',
        default=1.0,
        config_parameter='stock.green_zone_period'
    )
    critical_zone_period = fields.Float(
        string='Critical zone period',
        default=1.0,
        config_parameter='stock.critical_zone_period'
    )
    buffer_change_period = fields.Float(
        string='Buffer change period(hours)',
        default=0.0,
        config_parameter='stock.buffer_change_period'
    )
