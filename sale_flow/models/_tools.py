# import pandas as pd
import base64
import numpy as np
from pprint import pformat
import io

import logging
_logger = logging.getLogger(__name__)

try:
    import tabula
except:
    _logger.warn('tabula not available. Please install "tabula-py" python package.')

try:
    from pdfminer.converter import TextConverter
    from pdfminer.pdfinterp import PDFPageInterpreter
    from pdfminer.pdfinterp import PDFResourceManager
    from pdfminer.pdfpage import PDFPage
except:
    _logger.warn('pdfminer.six not available. Please install "pdfminer.six" python package.')

def get_params(tables):
    params = {}
    for table in tables:

        for it in table._values:
            for i in it:
                if 'Вес(кг)' == i or 'Вес (кг)' == i:
                    index = np.where(it == i)[0][0]
                    if index + 1 <= it.size - 1:
                        next_element = index + 1
                        value = it[next_element]
                        if isinstance(value, str):
                            try:
                                params['weight'] = float(value.replace(',', '.'))
                            except ValueError as e:
                                _logger.info("Wrong Value: %s", e)
                        else:
                            next_element = next_element + 1
                            value = it[next_element]
                            if isinstance(value, str):
                                try:
                                    params['weight'] = float(value.replace(',', '.'))
                                except ValueError as e:
                                    _logger.info("Wrong Value: %s", e)
                if 'd' == i:
                    index = np.where(it == i)[0][0]
                    size = it.size - 1
                    if index < size:
                        value = it[index + 1]
                        if isinstance(value, str):
                            try:
                                params['d'] = float(value.replace(',', '.'))
                            except ValueError as e:
                                _logger.info("Wrong Value: %s", e)
                        elif isinstance(value, float) and value > 0:
                            params['d'] = value

                elif isinstance(i, str) and 'd ' in i:
                    new_list = i.split(' ')
                    if len(new_list) > 1:
                        try:
                            params['d'] = float(new_list[1].replace(',', '.'))
                        except ValueError as e:
                            _logger.info("Wrong Value: %s", e)

                if 'D' == i:
                    index = np.where(it == i)[0][0]
                    size = it.size - 1
                    if index < size:
                        value = it[index + 1]
                        if isinstance(value, str):
                            try:
                                params['D'] = float(value.replace(',', '.'))
                            except ValueError as e:
                                _logger.info("Wrong Value: %s", e)
                        elif isinstance(value, float) and value > 0:
                            params['D'] = value

                elif isinstance(i, str) and 'D ' in i:
                    new_list = i.split(' ')
                    if len(new_list) > 1:
                        try:
                            params['D'] = float(new_list[1].replace(',', '.'))
                        except ValueError as e:
                            _logger.info("Wrong Value: %s", e)

                if 'B' == i:
                    index = np.where(it == i)[0][0]
                    size = it.size - 1
                    if index < size:
                        value = it[index + 1]
                        if isinstance(value, str):
                            try:
                                params['B'] = float(value.replace(',', '.'))
                            except ValueError as e:
                                _logger.info("Wrong Value: %s", e)
                        elif isinstance(value, float) and value > 0:
                            params['B'] = value

                elif isinstance(i, str) and 'B ' in i:
                    new_list = i.split(' ')
                    if len(new_list) > 1:
                        try:
                            params['B'] = float(new_list[1].replace(',', '.'))
                        except ValueError as e:
                            _logger.info("Wrong Value: %s", e)
    return params

def open_files(path):
    try:
        _logger.info('-----------open_files------------- path %s', path)
        tables = tabula.read_pdf(path, pages='1', multiple_tables=True, java_options=["-Xmx2048m"])
        params = get_params(tables)
        _logger.info('-----------open_files------------- params %s', params)
        with open(path, 'rb') as fh:
            params['datas'] = base64.b64encode(fh.read())
            for page in PDFPage.get_pages(fh,
                                          caching=True,
                                          check_extractable=True):
                resource_manager = PDFResourceManager()
                fake_file_handle = io.StringIO()
                converter = TextConverter(resource_manager, fake_file_handle, codec='utf-8')
                page_interpreter = PDFPageInterpreter(resource_manager, converter)
                page_interpreter.process_page(page)

                text = fake_file_handle.getvalue()
                text_list = text.split('For reference only.')
                if len(text_list) > 1:
                    params['categ_name'] = text_list[0].strip()
                # close open handles
                converter.close()
                fake_file_handle.close()
        _logger.info('-----------open_files---------- params: %s', pformat(params))
        return params

    except Exception as e:
        _logger.info('-----------open_files---------- e: %s', pformat(e))