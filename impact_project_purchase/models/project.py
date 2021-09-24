# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    @api.depends('purchase_request_ids')
    def _compute_purchase_request(self):
        for project in self:
            project.purchase_request_count = len(project.purchase_request_ids)

    @api.depends('purchase_request_line_ids')
    def _compute_purchase_request_line(self):
        for project in self:
            project.purchase_request_line_count = len(project.purchase_request_line_ids)

    @api.depends('purchase_ids')
    def _compute_purchases(self):
        for project in self:
            project.purchase_count = len(project.purchase_ids)

    @api.depends('purchase_order_line_ids')
    def _compute_purchase_order_line(self):
        for project in self:
            project.purchase_order_line_count = len(project.purchase_order_line_ids)

    @api.depends('purchase_stock_picking_ids')
    def _compute_stock_picking(self):
        for project in self:
            project.purchase_stock_picking_count = len(project.purchase_stock_picking_ids)

    @api.depends('purchase_account_move_ids')
    def _compute_account_move(self):
        for project in self:
            project.purchase_account_move_count = len(project.purchase_account_move_ids)

    @api.depends('purchase_account_payment_ids')
    def _compute_account_payment(self):
        for project in self:
            project.purchase_account_payment_count = len(project.purchase_account_payment_ids)

    purchase_request_ids = fields.One2many(
        comodel_name='purchase.request',
        inverse_name='construction_project_id',
        string='Purchase request',
    )

    purchase_request_line_ids = fields.One2many(
        comodel_name='purchase.request.line',
        inverse_name='construction_project_id',
        string='Purchase request line',
    )

    purchase_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='construction_project_id',
        string='Purchases',
    )

    purchase_order_line_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='construction_project_id',
        string='Purchase order line',
    )

    purchase_stock_picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='construction_project_id',
        string='Stock pickings',
    )

    purchase_account_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='construction_project_id',
        string='Account move',
    )

    purchase_account_payment_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='construction_project_id',
        string='Account payment',
    )

    purchase_request_count = fields.Integer(
        string='Purchase request count',
        compute='_compute_purchase_request',
        store=True,
    )

    purchase_request_line_count = fields.Integer(
        string='Purchase request line count',
        compute='_compute_purchase_request_line',
        store=True,
    )

    purchase_count = fields.Integer(
        string='Purchase count',
        compute='_compute_purchases',
        store=True,
    )

    purchase_order_line_count = fields.Integer(
        string='Purchase line count',
        compute='_compute_purchase_order_line',
        store=True,
    )

    purchase_stock_picking_count = fields.Integer(
        string='Stock picking count',
        compute='_compute_stock_picking',
        store=True,
    )

    purchase_account_move_count = fields.Integer(
        string='Account move count',
        compute='_compute_account_move',
        store=True,
    )

    purchase_account_payment_count = fields.Integer(
        string='Account payment count',
        compute='_compute_account_payment',
        store=True,
    )

    def button_new_purchase_request_action(self):
        f=6
        return {
            'name': _('New purchase request'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.request',
            'target': 'new',
            'context': {
                'default_construction_project_id': self.id,
                # 'default_location_dest_id': self.stock_location_id.id,
                'default_picking_type_id': self.receipt_picking_type_id.id,
            },
        }

    def button_purchase_request_action(self):
        return {
            'name': _('Purchase request'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.request',
            'domain': [('id', 'in', self.purchase_request_ids.ids)],
        }

    def button_purchase_request_line_action(self):
        return {
            'name': _('Purchase request line'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'purchase.request.line',
            'domain': [('id', 'in', self.purchase_request_line_ids.ids)],
        }

    def button_new_purchase_action(self):
        return {
            'name': _('New purchase order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'target': 'new',
            'context': {
                'default_construction_project_id': self.id,
                'default_location_dest_id': self.stock_location_id.id,
                'default_picking_type_id': self.receipt_picking_type_id.id,
            },
        }

    def button_purchase_action(self):
        return {
            'name': _('Purchase order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_ids.ids)],
        }

    def button_purchase_order_line_action(self):
        return {
            'name': _('Purchase order line'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,pivot,graph',
            'res_model': 'purchase.order.line',
            'domain': [('id', 'in', self.purchase_order_line_ids.ids)],
        }

    def button_stock_picking_action(self):
        return {
            'name': _('Stock picking'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', self.purchase_stock_picking_ids.ids)],
        }

    def button_account_move_action(self):
        return {
            'name': _('Account move'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.purchase_account_move_ids.ids)],
        }

    def button_account_payment_action(self):
        return {
            'name': _('Account_payments'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('id', 'in', self.purchase_account_payment_ids.ids)],
        }

    # def get_project_stock_location_from_context(self):
    #     model = self.env.context.get('active_model', None)
    #     active_id = self.env.context.get('active_id', None)
    #     if model == 'project.project' and active_id:
    #         project = self.env[model].browse(active_id)
    #         if project:
    #             location = project.receipt_picking_type_id
    #             return location
