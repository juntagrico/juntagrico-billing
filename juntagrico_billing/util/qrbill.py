from decimal import Decimal, ROUND_HALF_UP
from qrbill.bill import QRBill
from stdnum.ch.esr import calc_check_digit, validate, compact
import stdnum.iban
from lxml import etree
from io import StringIO
from juntagrico.config import Config


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


def bill_id_from_refnumber(refnumber):
    validate(refnumber)
    refnumber = compact(refnumber)[:-1]

    bill_part = refnumber[-10:]
    return int(bill_part)


def member_id_from_refnumber(refnumber):
    validate(refnumber)
    refnumber = compact(refnumber)[:-1]

    member_part = refnumber[-20:-10]
    return int(member_part)


def modify_svg_fill(svg_string, fill_value):
    """
    modify the fill value of the outermost rect in the qrbill svg.
    is used to modify the default svg output of qrbill from white to none.
    """
    svg = etree.fromstring(svg_string)

    rect = svg.find('.//rect', svg.nsmap)
    if rect is None:
        rect.set('fill', fill_value)

    return etree.tostring(svg)


def get_qrbill_svg(bill, paymenttype):
    """
    Get the QR-Bill payment part as SVG
    """
    addr = Config.organisation_address()
    if is_qr_iban(paymenttype.iban):
        refnr = calc_refnumber(bill)
        info = ''
    else:
        refnr = None
        info = str(bill.id)

    qr = QRBill(
        language='de',
        account=stdnum.iban.compact(paymenttype.iban),
        reference_number=refnr,
        additional_information=info,
        amount=Decimal(bill.amount_open).quantize(Decimal('.01'), ROUND_HALF_UP),
        creditor={
            'name': addr['name'],
            'street': addr['street'],
            'house_num': addr['number'],
            'pcode': addr['zip'],
            'city': addr['city'],
            'country': 'CH',
        },
        debtor={
            'name': '%s %s' % (
                bill.member.first_name,
                bill.member.last_name),
            'street': bill.member.addr_street,
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
