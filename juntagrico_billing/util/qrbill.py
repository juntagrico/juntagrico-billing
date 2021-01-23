from qrbill.bill import QRBill
from stdnum.ch.esr import calc_check_digit
import stdnum.iban
from lxml import etree
from io import StringIO

def is_qr_iban(iban):
    """
    Determine is an IBAN account number is
    a QR-IBAN used with swiss qr bills.
    If the 2nd group starts with 3 it is
    a QR-IBAN.
    """
    if not stdnum.iban.is_valid(iban):
        return False

    compacted = stdnum.iban.compact(iban)
    return compacted[4] == '3'


def calc_refnumber(bill):
    """
    QR-Bill reference number is identical to
    the ESR reference number.
    It consists von 26 digits + check-digit.

    We use the lower 10 digits for bill id
    and the next 10 digits for member id
    """
    bill_part = str(bill.id).rjust(10, '0')
    member_part = str(bill.member.id)

    ref_num = member_part + bill_part
    return ref_num + calc_check_digit(ref_num)


def modify_svg_fill(svg_string, fill_value):
    """
    modify the fill value of the outermost rect the qrbill svg.
    is used to modify the default svg output of qrbill from white to none.
    """
    svg = etree.fromstring(svg_string)

    rect = svg.find('.//rect', svg.nsmap)
    if rect != None:
        rect.set('fill', fill_value)

    return etree.tostring(svg)


def get_qrbill_svg(bill, paymenttype):
    """
    Get the QR-Bill payment part as SVG
    """
    if not is_qr_iban(paymenttype.iban):
        raise Exception('iban is no qr iban: %s' % paymenttype.iban)

    qr = QRBill(
                language='de',
                account=stdnum.iban.compact(paymenttype.iban),
                ref_number=calc_refnumber(bill),
                creditor={
                    'name': 'Genossenschaft ortoloco', 
                    'pcode': '8953', 
                    'city': 'Dietikon', 
                    'country': 'CH',
                },
                debtor={
                    'name': '%s %s' % (bill.member.first_name, bill.member.last_name),
                    'pcode': bill.member.addr_zipcode,
                    'city': bill.member.addr_location,
                    'country': 'CH',
                }
    )
    str_io = StringIO()
    qr.as_svg(str_io)
    svg_bytes = str_io.getvalue().encode('utf8')
    svg_bytes = modify_svg_fill(svg_bytes, 'none')

    return svg_bytes.decode('utf8')
