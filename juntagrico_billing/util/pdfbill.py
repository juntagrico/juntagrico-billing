import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from django.utils.formats import get_format
from django.utils.dateformat import format
from django.utils.translation import gettext as _
from juntagrico.config import Config
from juntagrico_billing.entity.settings import Settings
from juntagrico_billing.util.qrbill import get_qrbill_svg, is_qr_iban
from stdnum.exceptions import InvalidChecksum
from svglib.svglib import SvgRenderer
from reportlab.graphics.renderPM import drawToFile
from lxml import etree


def date_format(date):
    fmt = get_format('SHORT_DATE_FORMAT')
    return format(date, fmt)


def render_pdf_bill(bill, outfile):
    """
    render a bill as PDF in to a byte file-like output.
    """
    #
    # define styles
    #
    org_heading = getSampleStyleSheet()['Heading1']

    normal = ParagraphStyle(name='Normal')
    normalright = ParagraphStyle('Normal-Right', parent=normal, alignment=2)
    text = ParagraphStyle(name='Text', parent=normal, spaceBefore=6)
    heading1 = ParagraphStyle('Heading1', parent=normal, fontName=org_heading.fontName,
                                fontSize=14, leading=18,
                                spaceBefore=12, spaceAfter=6)
    heading2 = ParagraphStyle('Heading2', parent=normal, fontName=org_heading.fontName,
                                spaceBefore=6, spaceAfter=2)

    table_style = [
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),    # left align all cells
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),    # valign top all cells
        ('TOPPADDING', (0, 0), (-1, -1), 1),    # reduce top and bottom padding (default is 3)
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (0, -1), 0)     # right align last row
    ]

    story = []

    story.append(Spacer(1, 2*cm))

    #
    # table with addresses
    #
    addr = Config.organisation_address()
    org_address = Paragraph(
                            '<br/>'.join([addr['name'],
                                      '%s %s' % (addr['street'], addr['number']),
                                      '%s %s' % (addr['zip'], addr['city'])]),
                            normal
                            )
    memb = bill.member
    memb_address = Paragraph(
                            '<br/>'.join(['%s %s' % (memb.first_name, memb.last_name),
                                      memb.addr_street,
                                      '%s %s' % (memb.addr_zipcode, memb.addr_location)]),
                            normal
                            )

    address_table = Table([[org_address, memb_address]], style=table_style)
    story.append(address_table)

    story.append(Spacer(1, 3*cm))

    #
    # table with title and date
    #
    title = Paragraph('%s %d' % (_('Bill'), bill.id), heading1)
    date = Paragraph(date_format(bill.bill_date), normalright)  # right-align
    title_table = Table([(title, date)], style=table_style)
    story.append(title_table)

    #
    # billing period
    #
    period = Paragraph('%s %s - %s' % 
                        (_('Period'),
                         date_format(bill.business_year.start_date),
                         date_format(bill.business_year.end_date)),
                        normal)
    story.append(period)

    story.append(Spacer(1, 0.5*cm))

    #
    # bill items
    #
    lines=[]
    for item in bill.items.all():
        lines.append((Paragraph(item.description, normal),
                      Paragraph('%10.2f' % item.amount, normalright)))
    lines.append((Paragraph('<b>Total</b>', normal), Paragraph('<b>%10.2f</b>' % bill.amount, normalright)))

    bill_table = Table(lines, (None, 2*cm), style=table_style)
    story.append(bill_table)

    #
    # public notes
    #
    if bill.public_notes:
        story.append(Paragraph(bill.public_notes, text))

    #
    # payments
    #
    if bill.payments.all():
        story.append(Paragraph('<b>%s %s</b>' % (_('Payments per'), date_format(datetime.date.today())), heading2))

        lines=[]
        sum = 0.0
        for payment in bill.payments.all():
            lines.append((date_format(payment.paid_date), payment.type, Paragraph('%10.2f' % payment.amount, normalright)))
            sum += payment.amount

        lines.append((Paragraph(_('Total payments'), normal), '', Paragraph('%10.2f' % sum, normalright)))
        if sum < bill.amount:
            lines.append((Paragraph(_('Amount open yet'), normal), '', Paragraph('<b>%10.2f</b>' % (bill.amount - sum), normalright)))

        payments_table = Table(lines, (4*cm, None, 2*cm), style=table_style)
        story.append(payments_table)

        if sum >= bill.amount:
            story.append(Paragraph(_('Bill paid completely'), normal))

    #
    # payment notice
    # todo: make setting for due date notice link
    #
    story.append(Paragraph('%s %s.' % (_('The billed amount is due for payment according to the due date notice found here:'),
                                        'https://ortoloco.ch/dokumente/FäHi_2021.pdf'), text))

    #
    # add QR-Bill part if QR-IBAN
    #
    settings = Settings.objects.first()
    payment_type = settings.default_paymenttype
    if is_qr_iban(payment_type.iban):
        qr_svg = get_qrbill_svg(bill, payment_type)
        svg_element = etree.fromstring(qr_svg)

        renderer = SvgRenderer("")
        qrpayslip_drawing = renderer.render(svg_element)
    else:
        qrpayslip_drawing = None

        story.append(Spacer(1, 2*cm))

        # if no qr payslip, display account info for payment
        story.append(Paragraph(_('Please pay specifying bill number to:'), text))
        story.append(Paragraph('%s<br/>%s<br/>' % (payment_type.iban,
                                                   payment_type.name), text))
        story.append(Paragraph('%s<br/>%s, %s %s' % (_('in favor of'),
                                                     addr['name'], addr['zip'], addr['city']), text))

    # offset bottom margin by height of payslip
    if qrpayslip_drawing != None:
        bottom_margin = qrpayslip_drawing.height
    else:
        bottom_margin = 2*cm

    # function to draw payslip at bottom of page
    def draw_payslip(canvas, document):
        if qrpayslip_drawing == None:
            return

        # draw payslip at the bottom of the page without borders
        canvas.saveState()
        qrpayslip_drawing.drawOn(canvas, 0, 0)
        canvas.restoreState()

    #
    # build the document
    #
    doc = SimpleDocTemplate(outfile, bottomMargin=bottom_margin)
    doc.build(story, onFirstPage=draw_payslip, onLaterPages=draw_payslip)
