    def button_validate(self):
        res = super(Picking, self).button_validate()
        if res == True:
            for piking in self:
                account_move = self.env['account.move'].create({
                    'company_id': piking.company_id.id,
                    'construction_project_id': piking.construction_project_id.id,
                    'user_id': piking.user_id.id,
                    'partner_id': piking.partner_id.id,
                    'move_type': 'in_invoice',
                    'name': 'From picking ' + piking.name,
                })
                for stock_move in piking.move_ids_without_package:
                    for stock_move_line in stock_move.move_line_ids:
                        self.env['account.move.line'].create({
                            'company_id': stock_move_line.company_id.id,
                            'partner_id': stock_move.partner_id.id,
                            'name': stock_move.name,
                            'display_name': stock_move.description_picking,
                            'move_id': account_move.id,
                            'price_unit': stock_move_line.sale_price,
                            'product_uom_id': stock_move_line.product_uom_id.id,
                            'product_uom_category_id': stock_move_line.product_uom_category_id.id,
                            'product_id': stock_move_line.product_id.id,
                            'account_id': stock_move_line.product_id.categ_id.property_stock_account_input_categ_id.id,
                            'analytic_account_id': piking.construction_project_id.analytic_account_id.id,
                            'quantity': stock_move_line.qty_done,
                        })
        return res

    # def button_validate(self):
    #     res = super(Picking, self).button_validate()
    #     if res == True:
    #         for piking in self:
    #             account_move = self.env['account.move'].create({
    #                 'company_id': piking.company_id.id,
    #                 'construction_project_id': piking.construction_project_id.id,
    #                 'user_id': piking.user_id.id,
    #                 'partner_id': piking.partner_id.id,
    #                 'move_type': 'in_invoice',
    #                 'name': 'From picking ' + piking.name,
    #             })
    #             for stock_move in piking.move_ids_without_package:
    #                 for stock_move_line in stock_move.move_line_ids:
    #                     account_move_line = self.env['account.move.line'].create({
    #                         # 'company_id': stock_move_line.company_id.id,
    #                         # 'partner_id': stock_move.partner_id.id,
    #                         # 'name': stock_move.name,
    #                         # 'display_name': stock_move.description_picking,
    #                         'move_id': account_move.id,
    #                         'price_unit': stock_move_line.sale_price,
    #                         # 'product_uom_id': stock_move_line.product_uom_id.id,
    #                         # 'product_uom_category_id': stock_move_line.product_uom_category_id.id,
    #                         'product_id': stock_move_line.product_id.id,
    #                         # 'account_id': stock_move_line.product_id.categ_id.property_stock_account_input_categ_id.id,
    #                         # 'analytic_account_id': piking.construction_project_id.analytic_account_id.id,
    #                         # 'quantity': stock_move_line.qty_done,
    #                         'reconciled': False,
    #                     })
    #                     account_move_line._compute_analytic_account()
    #                     account_move_line.quantity = stock_move_line.qty_done
    #                     account_move_line._onchange_mark_recompute_taxes()
    #     return res        