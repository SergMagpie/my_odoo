# -*- coding: utf-8 -*-
from odoo import api, fields, models


# Main RKB settings:
class RkbSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Keys containers:
    default_login = fields.Char(default_model='rkb.config.settings.container', string='Login')
    default_password = fields.Char(default_model='rkb.config.settings.container', string='Password')
