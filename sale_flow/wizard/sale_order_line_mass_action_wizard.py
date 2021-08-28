# -*- coding: utf-8 -*-
import base64
import logging
import os
import tempfile
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
import xlrd, mmap, xlwt

_logger = logging.getLogger(__name__)


class SaleOrderLineMassActionWizard(models.TransientModel):
    _name = "sale.order.line.mass.action.wizard"

    rkb_date_planned = fields.Many2one('rkb.planed.date', string='Planed Date', ondelete='restrict')

    def apply_action(self):
        for record in self:
            aaa_env = self.env['account.analytic.account']
            aaa_id = aaa_env.browse(self.env.context.get('aaa_id', False))
            if aaa_id and aaa_id.so_line:
                for line in aaa_id.so_line:
                    line.rkb_date_planned = record.rkb_date_planned