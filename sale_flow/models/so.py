import base64
from io import BytesIO
import pandas as pd
from odoo import api, fields, models, _
import datetime
from odoo.addons import decimal_precision as dp
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, Warning
import logging  #Get the logger

_logger = logging.getLogger(__name__) #Get the logger


class SoCrmOrderList(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.partner_id:
            self.payment_term_id = self.partner_id.property_payment_term_id
            self.rkb_delivery_type = self.partner_id.rkb_delivery_type
            self.rkb_delivery_condition = self.partner_id.rkb_delivery_condition
            self.carrier_id = self.partner_id.property_delivery_carrier_id
        else:
            self.payment_term_id = False
            self.rkb_delivery_type = False
            self.rkb_delivery_condition = False
            self.carrier_id = False
        return res

    @api.depends('order_line.product_uom_qty')
    def _qt_all(self):

        for order in self:
            total_qt = 0.0
            for line in order.order_line:
                total_qt += line.product_uom_qty
            order.update({
                'qt_total': total_qt
            })

    def set_delivery_date(self):
        for order in self.filtered(lambda order: order.state != 'sale'):
            order.rkb_delivery_date = date.today()

    @api.multi
    def print_quotation(self):
        # self.set_delivery_date()
        return self.env.ref('sale.action_report_saleorder').report_action(self)

    @api.multi
    def action_quotation_send(self):
        # self.set_delivery_date()
        quotation_send = super().action_quotation_send()

        data = [
            {
                'rkb_product_position': order_line.rkb_product_position,
                'internal_notes': order_line.internal_notes,
                'product_id': order_line.product_id.name,
                'product_uom_qty': order_line.product_uom_qty,
                'price_unit': order_line.price_unit,
                'price_subtotal': order_line.price_subtotal,
                'rkb_date_planned.name': order_line.rkb_date_planned.name,
                'manufacturer': 'RKB Europe SA',
                'rkb_description': order_line.rkb_description,
            } for order_line in self.order_line]

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df = pd.DataFrame(data)
        df.rename(columns={
            'rkb_product_position': '№',
            'internal_notes': 'Обозначение в заявке',
            'product_id': 'Обозначение RKB',
            'product_uom_qty': 'Кол-во, шт.',
            'price_unit': 'Цена, евро/шт.',
            'price_subtotal': 'Сумма, евро',
            'rkb_date_planned.name': 'Срок поставки',
            'manufacturer': 'Производитель',
            'rkb_description': 'Примечания',
        }, inplace=True)
        df = df.reindex(columns=[
            '№',
            'Обозначение в заявке',
            'Обозначение RKB',
            'Кол-во, шт.',
            'Цена, евро/шт.',
            'Сумма, евро',
            'Срок поставки',
            'Производитель',
            'Примечания',
        ])
        df.to_excel(writer, index=False)
        writer.save()
        output.seek(0)
        workbook = output.read()

        attachment = self.env['ir.attachment'].create({
            'name': _('KP_RKB - %s') % self.name,
            'type': 'binary',
            'datas': base64.b64encode(workbook),
            'datas_fname': 'KP_RKB_%s.xlsx' % self.name,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        mail = self.env['mail.template'].browse(quotation_send['context']['default_template_id'])
        mail.attachment_ids = [(6, 0, attachment.ids)]

        return quotation_send

    @api.multi
    def action_cancel(self):
        for order in self:
            order.rkb_delivery_date = False
        return self.write({'state': 'cancel'})

    @api.model
    def _default_rkb_vendor_id(self):
        partner = self.env['ir.model.data'].get_object('sale_flow', 'rkb_switzerland_res_vendor').id
        return partner

    @api.multi
    @api.depends('version')
    def get_ver(self):
        for r in self:
            r.display_version = 'v' + str(r.version) + '.0'

    @api.depends('rfq_ids')
    def _compute_rfq_ids(self):
        for order in self:
            x = 0
            for rfq in order.rfq_ids:
                if rfq.state != 'cancel':
                    x += 1
            order.rfq_count = x

    curator_id = fields.Many2one('res.users', 'Curator', related='user_id.partner_id.rkb_curator', readonly=True)
    rkb_customer_code = fields.Char('Customer code', related='partner_id.customer_number')

    rkb_delivery_type = fields.Many2one('rkb.delivery.type', string='Delivery Type', ondelete='restrict')
    rkb_delivery_condition = fields.Many2one('rkb.delivery.condition', 'Delivery Condition', default=False)
    rkb_quote_number = fields.Char('RFQ Number From RKB')
    rkb_date = fields.Char('Date')
    rkb_crm = fields.Char('CRM')
    rkb_operator = fields.Char('Operator')
    rkb_delivery_date = fields.Date('Deadline of Qoutation', default=fields.Datetime.to_string(fields.datetime.now() + timedelta(days=15)))
    rkb_final_customer = fields.Many2one('res.partner', string='Final Customer')

    qt_total = fields.Float(string='Total Quantity',
                            digits=dp.get_precision('Product Unit of Measure'),
                            default=0,
                            store=True, compute='_qt_all')

    version = fields.Integer('Ver.:', default=1, copy=False)
    display_version = fields.Char('Version', compute=get_ver, store=True)

    parent_id = fields.Many2one('sale.order', string='Last version', copy=False, readonly=True)
    parent_left = fields.Integer(copy=False)
    parent_right = fields.Integer(copy=False)

    child_ids = fields.One2many('sale.order', 'parent_id', string='Previous vrsions', copy=False)
    rkb_vendor_id = fields.Many2one('res.partner', string='Vendor', default=_default_rkb_vendor_id)
    analogue_order_list_ids = fields.One2many('sale.analouge.order.list',
                                              'so_id',
                                              copy=True,
                                              ondelete='cascade',
                                              string='Analogue Order list')
    new_ver = fields.Boolean()

    rfq_ids = fields.One2many('purchase.order', 'sale_id', 'Request for Quotations')
    rfq_count = fields.Integer('Request for Quotations', compute='_compute_rfq_ids')
    analytic_account_id = fields.Many2one(copy=True)

    @api.multi
    def action_view_so_lines(self):
        for rec in self:
            domain = [('order_id', '=', rec.id)]
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Sale Order Lines'),
                'view_type': 'form',
                'view_id': self.env.ref('sale_flow.sale_flow_sale_order_line_tree_view').id,
                'view_mode': 'tree',
                'res_model': 'sale.order.line',
                'target': 'current',
                'domain': domain,
            }
            return action

    @api.depends('order_line')
    def compute_so_lines(self):
        for rec in self:
            if rec.order_line:
                rec.so_lines_count = len(rec.order_line)

    so_lines_count = fields.Integer(compute=compute_so_lines, string=_('Quotatations'))

    @api.multi
    def action_view_purchase(self):
        rfqs = self.mapped('rfq_ids')
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        if len(rfqs) > 1:
            action['domain'] = [('id', 'in', rfqs.ids)]
        elif len(rfqs) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = rfqs.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_create_purchase(self):
        if not self.rkb_vendor_id:
            raise Warning(_("Please, choose a vendor"))

        rfq = self.env['purchase.order'].sudo().create({
                                                        'partner_id': self.rkb_vendor_id.id,
                                                        'sale_id': self.id,
                                                        'analytic_account_id': self.analytic_account_id.id,
                                                        'opportunity_id': self.opportunity_id.id,
                                                       }).id
        _logger.info('\n\n\n-->> action_create_purchase -- RFQ ID <<---, %s\n\n\n', rfq)
        for line in self.order_line:
            line = self.env['purchase.order.line'].sudo().new({
                'sequence': line.original_sequence_from_lead,
                'name': line.name,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'price_unit': line.purchase_price,
                'product_uom': line.product_uom.id,
                'date_planned': datetime.now(),
                'ordered_product_brand_name': line.ordered_product_brand_name.id,
                'discount': line.discount,
                'internal_notes': line.internal_notes,
                'rkb_product_position': line.rkb_product_position,
                'order_id': rfq,
              })
            line.onchange_product_id()
            line = line.create(line._convert_to_write(line._cache))
            _logger.info('\n\n\n !!!!!!!!!!!!! line !!!!!!!!!!!! %s \n\n\n', line.price_unit)
        for analogue_line in self.analogue_order_list_ids:
            self.env['purchase.order.line'].sudo().create({
                'sequence': analogue_line.original_sequence_from_lead,
                'name': analogue_line.analogue_id.name,
                'product_id': analogue_line.product_id.id,
                'ordered_product_name': analogue_line.analogue_id.id,
                'product_qty': analogue_line.qty,
                'price_unit': analogue_line.product_id.lst_price,
                'date_planned': datetime.now(),
                'internal_notes': analogue_line.internal_notes,
                'ordered_product_brand_name': analogue_line.analogue_product_name.id,
                'product_uom': analogue_line.product_id.uom_po_id.id,
                'order_id': rfq,
              })

    @api.multi
    def action_new_version(self):
        for rec in self:
            rec.new_ver = True
            new_so = rec.copy()
            new_so.version = rec.version + 1
            rec.parent_id = new_so.id
            for r in rec.child_ids:
                r.parent_id = new_so.id
            rec.action_cancel()
            for po in new_so.rfq_ids:
                po.unlink()
            form_view = self.env.ref('sale.view_order_form')
            return {
                    'name': _('New Version of Quotation'),
                    'res_model': 'sale.order',
                    'res_id': new_so.id,
                    'views': [(form_view.id, 'form')],
                    'type': 'ir.actions.act_window',
                    'target': 'inline'
                   }

    @api.multi
    def unlink(self):
        for r in self:
            if len(r.child_ids) > 0:
                raise UserError(_('You have to delete all Previous versions.'))
        return super(SoCrmOrderList, self).unlink()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.depends('product_uom_qty', 'price_unit')
    def _compute_sum_purchase_cost(self):
        for rec in self:
            rec.total_coast_rkb = rec.product_uom_qty * rec.price_unit

    original_sequence_from_lead = fields.Integer(string="Original Lead Sequence")
    rkb_description = fields.Char('Description')
    rkb_product_name = fields.Char('Name', related='product_id.product_tmpl_id.name')
    rkb_product_position = fields.Char('#', compute='_compute_sale_order_line_position', store=True)
    rkb_date_planned = fields.Many2one('rkb.planed.date', string='Planed Date', ondelete='restrict')
    rkb_product_note = fields.Text('Note')
    total_coast_rkb = fields.Float('Sum', digits=(16, 2), compute=_compute_sum_purchase_cost)
    ordered_product_name = fields.Many2one('analogue.catalogue', string="Name of Analogue")
    ordered_product_brand_name = fields.Many2one('res.partner', string='Brand of Analogue')
    product_uom_qty = fields.Float(digits=(16, 0))
    control_id = fields.Many2one(related='order_id.analytic_account_id', string='Contract')
    order_state = fields.Selection(related='order_id.state', string='Quotation state')
    internal_notes = fields.Char(string=_("Seller's notes"))

    @api.multi
    def print_quotation(self):
        return self.env.ref('sale.action_report_saleorder').report_action(self)

    @api.multi
    @api.depends('order_id.order_line')
    def _compute_sale_order_line_position(self):
        for rec in self:
            order_id = rec[0].order_id
            for i, line in enumerate(sorted(order_id.order_line, key=lambda l: l.sequence)):
                i += 1
                line.rkb_product_position = '{}{}'.format('0' if i < 10 else '', i)

    @api.multi
    def write(self, vals):
        for record in self:
            old_price_unit = record.price_unit
            old_discount = record.discount
            old_price_subtotal = record.price_subtotal

        rec = super(SaleOrderLine, self).write(vals)

        for record in self:
            info = '<ul><li>Product:' + str(record.product_id.name) + '</li>'
            if 'price_unit' in vals or 'discount' in vals:
                if 'price_unit' in vals:
                    info += '<li>Price manually changed ' + str(old_price_unit) + ' -> ' + str(record.price_unit) + '</li>'
                if 'discount' in vals:
                    info += '<li>Discount manually changed ' + str(
                        old_discount) + ' -> ' + str(record.discount) + '</li>'

                info += '<li>Price subtotal manually changed ' + str(
                    old_price_subtotal) + ' -> ' + str(record.price_subtotal) + '</li></ul>'

                record.order_id.message_post(body=info)

        return rec

    @api.model
    def create(self, vals):
        New_id = super(SaleOrderLine, self).create(vals)
        zero_product = self.env['ir.model.data'].get_object('sale_flow', 'product_product_0').id
        if New_id.product_id.id == zero_product:
            New_id.unlink()
        else:
            if New_id.ordered_product_name:

                for prod in New_id.order_id.opportunity_id.order_list_ids:
                    if New_id.product_id == prod.product_id:
                        New_id.internal_notes = prod.internal_notes

                New_id.ordered_product_name.product_id = New_id.product_id.id

                for rec in New_id.order_id.analogue_order_list_ids:
                    if rec.analogue_id.id == New_id.ordered_product_name.id:
                        New_id.internal_notes = rec.internal_notes
                        rec.unlink()

            info = '<ul><li>Product :' + str(New_id.product_id.name) + '</li>'
            if New_id.price_unit or New_id.discount:
                if 'price_unit' in vals:
                    info += '<li>Price : ' + str(New_id.price_unit) + '</li>'
                if 'discount' in vals:
                    info += '<li>Discount :' + str(New_id.discount) + '</li>'
                info += '<li>Price subtotal : ' + str(New_id.price_subtotal) + '</li></ul>'
                New_id.order_id.message_post(body=info)

        return New_id


class AnalogueProductOrderList(models.Model):
    _name = "sale.analouge.order.list"

    @api.multi
    @api.onchange('analogue_id')
    def onchange_analogue_id(self):
        for r in self:
            if r.analogue_id.product_id:
                r.product_id = r.analogue_id.product_id.id

    original_sequence_from_lead = fields.Integer(string="Original Lead Sequence")
    analogue_id = fields.Many2one('analogue.catalogue', string="Name of Analogue")
    analogue_product_name = fields.Many2one(related='analogue_id.analogue_brand', string='Brand of Analogue')
    internal_notes = fields.Char(string="Seller's notes")
    product_id = fields.Many2one('product.product', string='RKB Product')
    qty = fields.Float('Quantity')
    so_id = fields.Many2one('sale.order')
    control_id = fields.Many2one(related='so_id.analytic_account_id', string='Contract')
    order_state = fields.Selection(related='so_id.state', string='Quotation state')

