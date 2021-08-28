# -*- coding: utf-8 -*-
from openerp import models, api, fields

import logging
_logger = logging.getLogger(__name__)

class ProductToCrmLeadWizardLine(models.TransientModel):

    _name = 'product.to.crm.lead.wizard.line'

    name = fields.Char('Name')
    qty = fields.Float('Quantity', default=1.0)
    wizard_id = fields.Many2one('product.to.crm.lead.wizard', 'Lead/Opportunity')

class ProductToCrmLeadWizard(models.TransientModel):

    _name = 'product.to.crm.lead.wizard'

    def _default_line_ids(self):
        active_ids = self.env.context.get('active_ids', False)
        if active_ids:
            prod_tpl_ids = self.env['product.template'].browse(active_ids)
            if prod_tpl_ids:
                line_ids = []
                for prod in prod_tpl_ids:
                    vals = {
                        'name': prod.name,
                        'qty': 1.0
                    }
                    line_ids.append((0, 0, vals))
                return line_ids

    crm_lead_id = fields.Many2one('crm.lead', 'Lead/Opportunity')
    crm_lead_new = fields.Boolean('New Lead/Opportunity')
    crm_lead_new_name = fields.Char('New Lead/Opportunity Name')
    crm_lead_new_partner_id = fields.Many2one('res.partner', string='Customer')
    line_ids = fields.One2many('product.to.crm.lead.wizard.line', 'wizard_id', default=_default_line_ids, string='Order Lines')

    @api.onchange('crm_lead_id')
    def onchange_crm_lead_id(self):
        if self.crm_lead_id:
            self.crm_lead_new = False
            self.crm_lead_new_name = False

    @api.onchange('crm_lead_new')
    def onchange_crm_lead_new(self):
        if self.crm_lead_new:
            self.crm_lead_id = False

    @api.multi
    def action_apply(self):
        crm_lead_id = False
        if self.crm_lead_id:
            crm_lead_id = self.crm_lead_id
        if self.crm_lead_new and self.crm_lead_new_name:
            crm_lead_new_vals = {
                'name': self.crm_lead_new_name,
                'partner_id': self.crm_lead_new_partner_id.id or False,
            }
            crm_lead_id = self.env['crm.lead'].create(crm_lead_new_vals)

        if crm_lead_id:
            order_list_lines = []
            cont = 0
            if crm_lead_id:
                for line in self.line_ids:
                    cont += 1
                    vals = {
                        'ordered_product': line.name,
                        'qty': line.qty,
                    }
                    order_list_lines.append((0, 0, vals))

                crm_lead_id.order_list_ids = order_list_lines
            self.crm_lead_id = crm_lead_id.id

    def action_apply_and_view(self):
        self.action_apply()
        if self.crm_lead_id:
            if self.crm_lead_id.type == 'lead':
                action = self.env.ref('crm.crm_lead_all_leads').read()[0]
                action['views'] = [(self.env.ref('crm.crm_case_form_view_leads').id, 'form')]
            else:
                action = self.env.ref('crm.crm_lead_opportunities_tree_view').read()[0]
                action['views'] = [(self.env.ref('crm.crm_case_form_view_oppor').id, 'form')]
            action['target'] = 'inline'
            action['res_id'] = self.crm_lead_id.id
            return action