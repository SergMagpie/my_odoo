# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProjectRelatives(models.Model):
    _inherit = 'project.project'


    def _compute_purchase_request_relatives(self):
        for project in self:
            project.purchase_request_count_relatives = len(project.purchase_request_relatives_ids)

    def _compute_purchase_request_line_relatives(self):
        for project in self:
            project.purchase_request_line_count_relatives = len(project.purchase_request_line_relatives_ids)

    def _compute_purchases_relatives(self):
        for project in self:
            project.purchase_count_relatives = len(project.purchase_relatives_ids)

    def _compute_purchase_order_line_relatives(self):
        for project in self:
            project.purchase_order_line_count_relatives = len(project.purchase_order_line_relatives_ids)

    def _compute_stock_picking_relatives(self):
        for project in self:
            project.purchase_stock_picking_count_relatives = len(project.purchase_stock_picking_relatives_ids)

    def _compute_account_move_relatives(self):
        for project in self:
            project.purchase_account_move_count_relatives = len(project.purchase_account_move_relatives_ids)

    def _compute_account_payment_relatives(self):
        for project in self:
            project.purchase_account_payment_count_relatives = len(project.purchase_account_payment_relatives_ids)

    purchase_request_relatives_ids = fields.One2many(
        comodel_name='purchase.request',
        compute='_compute_purchase_request_relatives_ids',
        string='Purchase request relatives',
    )

    purchase_request_line_relatives_ids = fields.One2many(
        comodel_name='purchase.request.line',
        compute='_compute_purchase_request_line_relatives_ids',
        string='Purchase request line relatives',
    )

    purchase_relatives_ids = fields.One2many(
        comodel_name='purchase.order',
        compute='_compute_purchase_relatives_ids',
        string='Purchases relatives',
    )

    purchase_order_line_relatives_ids = fields.One2many(
        comodel_name='purchase.order.line',
        compute='_compute_purchase_order_line_relatives_ids',
        string='Purchase order line relatives',
    )

    purchase_stock_picking_relatives_ids = fields.One2many(
        comodel_name='stock.picking',
        compute='_compute_purchase_stock_picking_relatives_ids',
        string='Stock pickings relatives',
    )

    purchase_account_move_relatives_ids = fields.One2many(
        comodel_name='account.move',
        compute='_compute_purchase_account_move_relatives_ids',
        string='Account move relatives',
    )

    purchase_account_payment_relatives_ids = fields.One2many(
        comodel_name='account.payment',
        compute='_compute_purchase_account_payment_relatives_ids',
        string='Account payment relatives',
    )

    purchase_request_count_relatives = fields.Integer(
        string='Purchase request count relatives',
        compute='_compute_purchase_request_relatives',
    )

    purchase_request_line_count_relatives = fields.Integer(
        string='Purchase request line count relatives',
        compute='_compute_purchase_request_line_relatives',
    )

    purchase_count_relatives = fields.Integer(
        string='Purchase count relatives',
        compute='_compute_purchases_relatives',
    )

    purchase_order_line_count_relatives = fields.Integer(
        string='Purchase line count relatives',
        compute='_compute_purchase_order_line_relatives',
    )

    purchase_stock_picking_count_relatives = fields.Integer(
        string='Stock picking count relatives',
        compute='_compute_stock_picking_relatives',
    )

    purchase_account_move_count_relatives = fields.Integer(
        string='Account move count relatives',
        compute='_compute_account_move_relatives',
    )

    purchase_account_payment_count_relatives = fields.Integer(
        string='Account payment count relatives',
        compute='_compute_account_payment_relatives',
    )
    #
    # def button_new_purchase_request_relatives_action(self):
    #     return {
    #         'name': _('New purchase request relatives'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'purchase.request',
    #         'target': 'new',
    #         'context': {
    #             'default_construction_project_id': self.id,
    #             # 'default_location_dest_id': self.stock_location_id.id,
    #             'default_picking_type_id': self.receipt_picking_type_id.id,
    #         },
    #     }

    def button_purchase_request_relatives_action(self):
        return {
            'name': _('Purchase request relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.request',
            'domain': [('id', 'in', self.purchase_request_relatives_ids.ids)],
        }

    def button_purchase_request_line_relatives_action(self):
        return {
            'name': _('Purchase request line relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'purchase.request.line',
            'domain': [('id', 'in', self.purchase_request_line_relatives_ids.ids)],
        }
    #
    # def button_new_purchase_action(self):
    #     return {
    #         'name': _('New purchase order'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'purchase.order',
    #         'target': 'new',
    #         'context': {
    #             'default_construction_project_id': self.id,
    #             'default_location_dest_id': self.stock_location_id.id,
    #             'default_picking_type_id': self.receipt_picking_type_id.id,
    #         },
    #     }

    def button_purchase_relatives_action(self):
        return {
            'name': _('Purchase order relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_relatives_ids.ids)],
        }

    def button_purchase_order_line_relatives_action(self):
        return {
            'name': _('Purchase order line relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'purchase.order.line',
            'domain': [('id', 'in', self.purchase_order_line_relatives_ids.ids)],
        }

    def button_stock_picking_relatives_action(self):
        return {
            'name': _('Stock picking relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', self.purchase_stock_picking_relatives_ids.ids)],
        }

    def button_account_move_relatives_action(self):
        return {
            'name': _('Account move relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.purchase_account_move_relatives_ids.ids)],
        }

    def button_account_payment_relatives_action(self):
        return {
            'name': _('Account_payments relatives'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('id', 'in', self.purchase_account_payment_relatives_ids.ids)],
        }

    # def get_project_stock_location_from_context(self):
    #     model = self.env.context.get('active_model', None)
    #     active_id = self.env.context.get('active_id', None)
    #     if model == 'project.project' and active_id:
    #         project = self.env[model].browse(active_id)
    #         if project:
    #             location = project.receipt_picking_type_id
    #             return location

    def _compute_purchase_request_relatives_ids(self):
        for project in self:
            project.purchase_request_relatives_ids = project._get_child().purchase_request_ids

    def _compute_purchase_request_line_relatives_ids(self):
        for project in self:
            project.purchase_request_line_relatives_ids = project._get_child().purchase_request_line_ids

    def _compute_purchase_relatives_ids(self):
        for project in self:
            project.purchase_relatives_ids = project._get_child().purchase_ids

    def _compute_purchase_order_line_relatives_ids(self):
        for project in self:
            project.purchase_order_line_relatives_ids = project._get_child().purchase_order_line_ids

    def _compute_purchase_stock_picking_relatives_ids(self):
        for project in self:
            project.purchase_stock_picking_relatives_ids = project._get_child().purchase_stock_picking_ids

    def _compute_purchase_account_move_relatives_ids(self):
        for project in self:
            project.purchase_account_move_relatives_ids = project._get_child().purchase_account_move_ids

    def _compute_purchase_account_payment_relatives_ids(self):
        for project in self:
            project.purchase_account_payment_relatives_ids = project._get_child().purchase_account_payment_ids

    def _get_child(self):
        # while self.parent_id:
        #     self = self.parent_id
        rez = self.env['project.project'].search([('id', 'child_of', self.id)])
        return rez