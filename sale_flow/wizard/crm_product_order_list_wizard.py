# -*- coding: utf-8 -*-
import base64
import logging
import os
import tempfile
from odoo.exceptions import UserError
from odoo import api, fields, models, _, SUPERUSER_ID
import xlrd, mmap, xlwt

_logger = logging.getLogger(__name__)


class CRMProductOrderListWizard(models.TransientModel):
    _name = "crm.product.order.list.wizard"

    file_data = fields.Binary('Product File', required=True, )
    file_name = fields.Char('File Name')

    def import_button(self):
        if not self.csv_validator(self.file_name):
            raise UserError(_("The file must be an .xls/.xlsx extension"))
        file_path = tempfile.gettempdir() + '/file.xlsx'
        data = self.file_data
        f = open(file_path, 'wb')
        f.write(base64.b64decode(data))
        f.close()

        workbook = xlrd.open_workbook(file_path, on_demand=True)
        worksheet = workbook.sheet_by_index(0)
        first_row = []  # The row where we stock the name of the column
        for col in range(worksheet.ncols):
            first_row.append(worksheet.cell_value(0, col))
        # transform the workbook to a list of dictionaries
        archive_lines = []
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        crm_lead_obj = self.env['crm.lead']

        self.valid_columns_keys(archive_lines)

        crm_lead_id = crm_lead_obj.browse(self.env.context.get('lead_id', False))
        order_list_lines = []
        cont = 0
        if crm_lead_id:
            for line in archive_lines:
                cont += 1
                name = line.get(u'name', "")
                if isinstance(name, float):
                    name = str(name).strip()
                    name = name[:-2:]
                else:
                    name = str(name).strip()
                quantity = line.get(u'quantity', 0)
                vals = {
                    'ordered_product': name,
                    'qty': quantity,
                }
                order_list_lines.append((0, 0, vals))

            crm_lead_id.order_list_ids = order_list_lines

        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def valid_columns_keys(self, archive_lines):
        columns = archive_lines[0].keys()
        print
        "columns>>", columns
        text = "The file must contain the following columns: name, quantity. \n The following columns are not in the file:";
        text2 = text
        if not 'name' in columns:
            text += "\n[ name ]"
        if not u'quantity' in columns:
            text += "\n[ quantity ]"
        if text != text2:
            raise UserError(text)
        return True

    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return True if extension == '.xls' or extension == '.xlsx' else False

