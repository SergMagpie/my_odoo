# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from ._tools import open_files

import logging  # Get the logger
_logger = logging.getLogger(__name__)  # Get the logger


OPTIONAL_PRICE_FIELD_MAPPING = {
    'option_price_first': 'option_markup_first',
    'option_price_second': 'option_markup_second',
    'option_price_third': 'option_markup_third'
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    list_price = fields.Float(
        string='Sales Price',
        default=0.0,
        digits=dp.get_precision('Product Price'),
        help='Base price to compute the customer price. Sometimes called the catalog price.'
    )
    option_price_first = fields.Float(
        company_dependent=True,
        digits=dp.get_precision('Product Price'),
        help='Price for the main company'
    )
    option_price_second = fields.Float(
        company_dependent=True,
        digits=dp.get_precision('Product Price'),
        help='Price for the second company'
    )
    option_price_third = fields.Float(
        company_dependent=True,
        digits=dp.get_precision('Product Price'),
        help='Price for the third company'
    )
    is_main_company = fields.Boolean(
        string='Main company?',
        compute='_compute_is_main_company',
        default=False
    )
    rkb_item_type = fields.Many2one(
        comodel_name='rkb.product.item.type',
        string='Item type'
    )
    rkb_sub_categ = fields.Char(
        string='Sub Category'
    )
    rkb_inner_diameter = fields.Float(
        string='Inner diameter',
        digits=dp.get_precision('Inner diameter'),
        help="The inner diameter in mm."
    )
    rkb_outer_diameter = fields.Float(
        string='Outer diameter',
        digits=dp.get_precision('Outer diameter'),
        help="The outer diameter in mm."
    )
    rkb_width = fields.Float(
        string='Width',
        digits=dp.get_precision('Width'),
        help="The width in mm."
    )
    rkb_additional_parameter = fields.Float(
        string='Additional parameter',
        digits=dp.get_precision('Additional parameter'),
        help="The additional parameter in mm."
    )
    rkb_pdf_drawing_name = fields.Char(
        string='PDF drawing Name'
    )
    rkb_pdf_drawing = fields.Binary(
        string='PDF drawing'
    )
    rkb_additional_comment = fields.Text(
        string='Additional comment'
    )
    analogs_ids = fields.One2many(
        comodel_name='analogue.catalogue',
        inverse_name='product_templ_id'
    )
    doc_parsed = fields.Boolean(
        string='Doc Parsed',
        default=False
    )
    parser_processed = fields.Boolean(
        string='Parser Processed',
        default=False
    )

    def _get_main_company(self):
        """
        Get main company in system
        :return: res.company (obj)
        """
        try:
            main_company = self.sudo().env.ref('base.main_company', raise_if_not_found=False)
        except ValueError:
            main_company = self.env['res.company'].sudo().search([], limit=1, order='id')
        return main_company

    def _get_optional_price(self, to_currency, price):
        """
        The function calculates the optional price using the formula:
        1. price -> convert in to company currency (base func. compute() in currency)
        2. rec.price + (rec.price / 100 * rec.rkb_item_type.duty) or 0
        :param to_currency: currency into which you want to convert the amount
        :param price: base price to be calculated (float)
        :return: optional_price (float)
        """
        from_currency = self._get_main_company().currency_id
        convert_price = from_currency.compute(price, to_currency)

        if self.rkb_item_type.duty != 0.0:
            optional_price = convert_price + (convert_price / 100 * self.rkb_item_type.duty)
        else:
            optional_price = convert_price

        return optional_price

    def _set_ir_property_product(self, field, price):
        """
        A function that creates 'ir.property' for a specific field for all companies in the system
        :param field: field to convert
        :param price: base price to be calculated (float)
        :return: True
        """
        for company in self.env['res.company'].search([('id', '!=', self._get_main_company().id)]):

            optional_price = self._get_optional_price(to_currency=company.currency_id, price=price)
            markup = getattr(company, OPTIONAL_PRICE_FIELD_MAPPING.get(field.name))
            optional_price = optional_price * markup if markup != 0.0 else optional_price

            self._cr.execute(
                """SELECT id FROM ir_property 
                   WHERE name=%s AND 
                   res_id=%s AND
                   company_id=%s 
                   LIMIT 1""", (field.name,
                                'product.template,%s' % self.id,
                                company.id))
            property_id = self._cr.fetchone()

            if property_id:
                actual_property = self.env['ir.property'].browse(property_id[0])
                actual_property.value_float = optional_price
            else:
                self.env['ir.property'].create({
                    'name': field.name,
                    'type': 'float',
                    'res_id': 'product.template,%s' % self.id,
                    'fields_id': field.id,
                    'value_float': optional_price,
                    'company_id': company.id
                })
        return True

    @api.multi
    def _compute_is_main_company(self):
        for rec in self:
            rec.is_main_company = True if self._get_main_company() == self.env.user.company_id else False

    @api.multi
    def write(self, vals):
        for record in self:
            res = super(ProductTemplate, record).write(vals)

            if any(field in vals for field in ('option_price_first', 'option_price_second', 'option_price_third')):
                # Fields that require recalculation for other companies
                trigger_fields = {'option_price_first', 'option_price_second', 'option_price_third'} & set(vals)
                for field in trigger_fields:
                    record._set_ir_property_product(
                        field=self.env['ir.model.fields']._get(record._name, field),
                        price=vals.get(field, 0.0))
            return res

    @api.model
    def create(self, vals):
        product = super(ProductTemplate, self).create(vals)

        trigger_fields = {
            'option_price_first': product.option_price_first,
            'option_price_second': product.option_price_second,
            'option_price_third': product.option_price_third
        }
        for field_name, field_value in trigger_fields.items():
            if field_value > 0:
                product._set_ir_property_product(
                    field=self.env['ir.model.fields']._get(self._name, field_name),
                    price=field_value)
        return product

    @api.model
    def default_get(self, fields_list):
        defaults = super(ProductTemplate, self).default_get(fields_list)
        if 'is_main_company' in defaults:
            defaults['is_main_company'] = True if self._get_main_company() == self.env.user.company_id else False
        return defaults

    @api.multi
    def _compute_currency_id(self):
        for template in self:
            template.currency_id = self.env.user.company_id.currency_id.id

    def _compute_cost_currency_id(self):
        for template in self:
            template.cost_currency_id = self._get_main_company().currency_id.id

    def get_rkb_categ(self, name):
        sub_categ = self.env['rkb.product.item.type.analog'].search([
            ('name', '=', name)
        ], limit=1)
        if sub_categ and sub_categ.rkb_categ_id:
            return sub_categ.rkb_categ_id
        else:
            return False

    def set_doc_pdf_fields(self, params):
        # with open(modules.get_module_resource('sale_flow', 'static/img', 'my_image.png'), 'rb') as f:
        vals = {}
        if 'datas' in params:
            vals['rkb_pdf_drawing'] = params['datas']
            vals['rkb_pdf_drawing_name'] = self.name + '.pdf'
        if 'd' in params:
            vals['rkb_inner_diameter'] = params['d']
        if 'D' in params:
            vals['rkb_outer_diameter'] = params['D']
        if 'B' in params:
            vals['rkb_width'] = params['B']
        if 'weight' in params:
            vals['weight'] = params['weight']
        if 'categ_name' in params:
            categ_id = self.get_rkb_categ(params['categ_name'])
            if categ_id:
                vals['rkb_item_type'] = categ_id.id
                if categ_id.code:
                    vals['ukt_zed'] = categ_id.code
        if vals:
            vals['doc_parsed'] = True
        if 'parser_processed' in params:
            vals['parser_processed'] = True
            _logger.info('--------------------- vals: %s', (vals))
            self.write(vals)

    def parse_doc_pdf(self):
        for record in self:
            if record.name and not record.rkb_pdf_drawing and not record.parser_processed:
                path = "/opt/rkb_docs_pdf/%s.pdf" % (record.name.replace(" ", ""))
                _logger.info('-------------parse_doc_pdf----------- path %s', path)
                params = open_files(path) or {}
                _logger.info('-------------parse_doc_pdf----------- params %s', params)
                params['parser_processed'] = True
                if params:
                    record.set_doc_pdf_fields(params)
        return True

    @api.model
    def product_doc_parser_cron(self):
        product_ids = self.env['product.template'].search([
            ('parser_processed', '=', False),
        ], order='id asc', limit=40)
        _logger.info('------------------------------- product_ids %s', product_ids)
        if product_ids:
            for product in product_ids:
                product.parse_doc_pdf()

    @api.model
    def product_rkb_category_cron(self):
        product_ids = self.env['product.template'].search([
            ('rkb_sub_categ', '!=', False),
        ], order='id asc')
        _logger.info('------------------------------- product_ids %s', product_ids)
        _logger.info('------------------------------- len(product_ids) %s', len(product_ids))
        if product_ids:
            for product in product_ids:
                categ_id = self.get_rkb_categ(product.rkb_sub_categ)
                if categ_id:
                    vals = {
                        'rkb_item_type': categ_id.id,
                    }
                    if categ_id.code:
                        vals['ukt_zed'] = categ_id.code
                    _logger.info('------------------------------- product %s', product)
                    _logger.info('------------------------------- vals %s', vals)
                    product.write(vals)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    @api.depends('name')
    def _compute_origin_display_name(self):
        for r in self:
            r.display_name = r.name

    display_name = fields.Char(
        string='Display name',
        compute=_compute_origin_display_name,
        store=True
    )
