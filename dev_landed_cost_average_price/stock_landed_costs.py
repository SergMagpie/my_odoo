# -*- coding: utf-8 -*-
##############################################################################
#
#    DevIntelle Solution(Odoo Expert)
#    Copyright (C) 2015 Devintelle Soluation (<http://devintellecs.com/>)
#
##############################################################################

from odoo import api, models, _
from odoo.exceptions import UserError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def get_valuation_lines(self):
        lines = []

        for move in self.mapped('picking_ids').mapped('move_lines'):
            # it doesn't make sense to make a landed cost for a product
            # that isn't set as being valuated in real time at real cost
            if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ['real', 'average', 'fifo']:
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.value,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_('The selected picking does not contain any move that would be impacted by landed costs. '
                              'Landed costs are only possible for products configured in real time valuation '
                              'with real price costing method. Please make sure it is the case, '
                              'or you selected the correct picking'))
        return lines

    @api.multi
    def button_validate(self):
        if any(cost.state != 'draft' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        if any(not cost.valuation_adjustment_lines for cost in self):
            raise UserError(_('No valuation adjustments lines. You should maybe recompute the landed costs.'))
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
            }
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                if line.product_id.categ_id.property_cost_method == 'average' and line.product_id.qty_available:
                    adjust_value = line.additional_landed_cost 
                    qty_available = line.product_id.qty_available
                    standard_price = line.product_id.standard_price
                    pro_price = (adjust_value + (qty_available * standard_price)) / qty_available
                    line.product_id.write({'standard_price': pro_price})
                # Prorate the value at what's still in stock
                cost_to_add = (line.move_id.remaining_qty / line.move_id.product_qty) * line.additional_landed_cost

                new_landed_cost_value = line.move_id.landed_cost_value + line.additional_landed_cost
                line.move_id.write({
                    'landed_cost_value': new_landed_cost_value,
                    'value': line.move_id.value + line.additional_landed_cost,
                    'remaining_value': line.move_id.remaining_value + cost_to_add,
                    'price_unit': (line.move_id.value + line.additional_landed_cost) / line.move_id.product_qty,
                })
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - line.move_id.remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move.post()
        return True


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []

        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])

        # Create account move lines for quants already out of stock
        ###############################################################################
        #           Fixed. This part of the function will be executed only if         #
        #     in the product category the pricing method is NOT Average Cost (AVCO)   #
        ###############################################################################
        if qty_out > 0 and self.product_id.categ_id.property_cost_method != 'average':
            debit_line = dict(base_line,
                              name=(self.name + ": " + str(qty_out) + _(' already out')),
                              quantity=0,
                              account_id=already_out_account_id)
            credit_line = dict(base_line,
                               name=(self.name + ": " + str(qty_out) + _(' already out')),
                               quantity=0,
                               account_id=debit_account_id)
            diff = diff * qty_out / self.quantity
            if diff > 0:
                debit_line['debit'] = diff
                credit_line['credit'] = diff
            else:
                # negative cost, reverse the entry
                debit_line['credit'] = -diff
                credit_line['debit'] = -diff
            AccountMoveLine.append([0, 0, debit_line])
            AccountMoveLine.append([0, 0, credit_line])

            # TDE FIXME: oh dear
            if self.env.user.company_id.anglo_saxon_accounting:
                debit_line = dict(base_line,
                                  name=(self.name + ": " + str(qty_out) + _(' already out')),
                                  quantity=0,
                                  account_id=credit_account_id)
                credit_line = dict(base_line,
                                   name=(self.name + ": " + str(qty_out) + _(' already out')),
                                   quantity=0,
                                   account_id=already_out_account_id)

                if diff > 0:
                    debit_line['debit'] = diff
                    credit_line['credit'] = diff
                else:
                    # negative cost, reverse the entry
                    debit_line['credit'] = -diff
                    credit_line['debit'] = -diff
                AccountMoveLine.append([0, 0, debit_line])
                AccountMoveLine.append([0, 0, credit_line])

        return AccountMoveLine
