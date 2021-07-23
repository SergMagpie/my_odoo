# import PyPDF2
# pdfFileObject = open('sample.pdf', 'rb')
# pdfReader = PyPDF2.PdfFileReader(pdfFileObject)
# count = pdfReader.numPages
# print(count)
# # for i in range(count):
# #     page = pdfReader.getPage(i)
# #     print(page.extractText())
# page = pdfReader.getPage(0)
# print(page.extractText())

import fitz  # this is pymupdf

with fitz.open("ODOO.pdf") as doc:
    # text = ""
    # print(doc.get_text("blocks"))
    for page in doc:
        block = page.get_text("blocks")
        for i in block:
            text = i[4] + str(int(i[1]))
            print(text)
        if input('next? ') == 'y':
            continue
        else:
            break


