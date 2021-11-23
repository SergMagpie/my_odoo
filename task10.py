import barcode
from barcode.writer import ImageWriter

def testEan():
    EAN = barcode.get_barcode_class('ean13')
    ean = EAN(u'123456789011', writer=ImageWriter())
    fullname = ean.save('my_ean13_barcode')

if __name__ == '__main__':
    testEan()