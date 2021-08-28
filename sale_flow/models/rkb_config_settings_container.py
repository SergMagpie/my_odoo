# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging
import pytz
_logger = logging.getLogger(__name__)


class PhonetSecure(models.Model):
	_name = 'rkb.config.settings.container'

	update_mode = fields.Boolean()
	login = fields.Char()
	password = fields.Char()

	def get_keys(self):
		keys = self.default_get(['login', 'password'])
		if 'login' in keys and 'password' in keys:
			return (keys['login'], keys['password'])
		else:
			raise Warning(_('RKB login and password was not properly set.'))
