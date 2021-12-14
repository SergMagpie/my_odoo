import base64
from io import BytesIO
from PIL import Image

import barcode
from barcode.writer import ImageWriter

from odoo import models, http
from odoo.http import request

# class DkBarcodeMaker(models.AbstractModel):
#     _name = 'dk.barcode.maker'
#
#     def create_barcode(self, code):
#         rv = BytesIO()
#         EAN = barcode.get_barcode_class('Code128')
#         options = dict(write_text=False)
#         EAN(code, writer=ImageWriter()).write(rv, options)
#         rv.seek(0)
#         barcode_file = rv.read()
#         barcode_record = base64.b64encode(barcode_file)
#         return barcode_record


def create_barcode(type, value, width=600, height=100, humanreadable=0, quiet=1, mask=None):
    """

    :param type: Accepted types: 'EAN8', 'EAN13', 'Code128', 'JAN', 'UPCA', 'ISBN13',
        'ISBN10', 'ISSN', 'Code39', 'PZN', 'Code128'
    :param value: barcode (str)
    :param width:
    :param height:
    :param humanreadable:
    :param quiet:
    :param mask:
    :return: BytesIO()
    """
    rv = BytesIO()
    EAN = barcode.get_barcode_class(type)
    options = dict(write_text=humanreadable)
    EAN(value, writer=ImageWriter()).write(rv, options)
    rv.seek(0)
    img = Image.open(rv)
    width = int(width)
    height = int(height)
    resized_img = img.resize((width, height), Image.ANTIALIAS)
    new_barcode_file = BytesIO()
    resized_img.save(new_barcode_file, 'png')
    new_barcode_file.seek(0)
    exiting_file = new_barcode_file.read()
    return exiting_file

class DkReportMaker(http.Controller):

    @http.route(['/report/dk-barcode', '/report/dk-barcode/<type>/<path:value>'], type='http', auth="public")
    def dk_report_barcode(self, type, value, width=600, height=100, humanreadable=0, quiet=1, mask=None):
        """Contoller able to render barcode images thanks to reportlab.
        Samples:
            <img t-att-src="'/report/dk-barcode/QR/%s' % o.name"/>
            <img t-att-src="'/report/dk-barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s' %
                ('QR', o.name, 200, 200)"/>

        :param type: Accepted types: 'Codabar', 'Code11', 'Code128', 'EAN13', 'EAN8', 'Extended39',
        'Extended93', 'FIM', 'I2of5', 'MSI', 'POSTNET', 'QR', 'Standard39', 'Standard93',
        'UPCA', 'USPS_4State'
        :param humanreadable: Accepted values: 0 (default) or 1. 1 will insert the readable value
        at the bottom of the output image
        :param quiet: Accepted values: 0 (default) or 1. 1 will display white
        margins on left and right.
        :param mask: The mask code to be used when rendering this QR-code.
                     Masks allow adding elements on top of the generated image,
                     such as the Swiss cross in the center of QR-bill codes.
        """
        #
        # barcode_file = BytesIO(b64decode(request.env['product.product'].create_barcode(value)))
        # new_barcode_file = BytesIO()
        # img = Image.open(barcode_file)
        # width = int(width)
        # height = int(height)
        # resized_img = img.resize((width, height), Image.ANTIALIAS)
        # resized_img.save(new_barcode_file, 'png')
        # new_barcode_file.seek(0)
        # exiting_file = new_barcode_file.read()
        exiting_file = create_barcode(type, value, width, height, humanreadable)

        return request.make_response(exiting_file, headers=[('Content-Type', 'image/png')])

