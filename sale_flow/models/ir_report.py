# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from base64 import b64decode
from logging import getLogger
from PIL import Image
import io
try:
    from PyPDF2 import PdfFileWriter, PdfFileReader  # pylint: disable=W0404
    from PyPDF2.utils import PdfReadError  # pylint: disable=W0404
except ImportError:
    pass
try:
    # we need this to be sure PIL has loaded PDF support
    from PIL import PdfImagePlugin  # noqa: F401
except ImportError:
    pass
logger = getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        result = super(IrActionsReport, self)._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

        if self.xml_id == 'sale.action_report_saleorder':
            doc = self.env['sale.order'].browse(res_ids)

            for rec in doc:

                user = self.env['res.users'].browse(self.env.uid)
                if not rec.company_id.add_watermark or rec.company_id.watermark_selection != 'letter_head':
                    return result
                else:
                    if rec.company_id.add_watermark and rec.company_id.watermark_selection == 'letter_head':
                        result = super(IrActionsReport, self)._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)
                        user = self.env['res.users'].browse(self.env.uid)
                        watermark = None
                        if rec.company_id.letter_head:
                            watermark = b64decode(rec.company_id.letter_head)
                        else:
                            if watermark:
                                watermark = b64decode(watermark)
                        if not watermark:
                            return result
                        pdf = PdfFileWriter()
                        pdf_watermark = None
                        watermark_streams = []
                        try:
                            pdf_watermark = io.BytesIO(watermark)
                            watermark_streams.append(pdf_watermark)
                            pdf_watermark = PdfFileReader(pdf_watermark)
                        except PdfReadError:
                            try:
                                image = Image.open(io.BytesIO(watermark))
                                pdf_buffer = io.BytesIO()
                                if image.mode != 'RGB':
                                    image = image.convert('RGB')
                                resolution = image.info.get('dpi', rec.company_id.paperformat_id.dpi or 90)
                                if isinstance(resolution, tuple):
                                    resolution = resolution[0]
                                image.save(pdf_buffer, 'pdf', resolution=resolution)
                                pdf_watermark = PdfFileReader(pdf_buffer)
                            except:
                                logger.exception("Failed To load watermark")
                        if not pdf_watermark:
                            logger.error('No usable watermark found, got s%...', watermark[:100])
                            return result

                        if pdf_watermark.numPages < 1:
                            logger.error('Your watermark pdf does contain any page')

                        if pdf_watermark.numPages > 1:
                            logger.debug('Your watermark pdf contains more than one page'
                                         'all but the first one be ignored')

                        # if rec.company_id.sale_order_custom_report_id.xml_id == 'rkb_email_parser.report_saleorder_document_rkb_trade':
                        if rec.company_id.sale_order_custom_report_id.xml_id == 'sale_flow.report_saleorder_document_rkb_trade':
                            watermark_from_first_page = True
                        else:
                            watermark_from_first_page = True

                        for number, page in enumerate(PdfFileReader(io.BytesIO(result)).pages):
                            watermark_page = pdf.addBlankPage(page.mediaBox.getWidth(), page.mediaBox.getHeight())
                            watermark_page.mergePage(page)
                            if number != 0 or watermark_from_first_page:
                                watermark_page.mergePage(pdf_watermark.getPage(0))
                            pdf_content = io.BytesIO()
                            pdf.write(pdf_content)
                        return pdf_content.getvalue()
        else:
            return result

##########################################################################################
