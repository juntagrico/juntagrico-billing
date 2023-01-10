import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from django.utils.formats import get_format
from django.utils.dateformat import format
from django.utils.translation import gettext as _
from juntagrico.config import Config
from juntagrico_billing.config import Config as BillingConfig
from juntagrico_billing.entity.settings import Settings
from juntagrico_billing.util.qrbill import get_qrbill_svg, is_qr_iban
from svglib.svglib import SvgRenderer
from lxml import etree


class PdfBillRenderer(object):

    def __init__(self):
        #
        # define styles
        #
        self.org_heading = getSampleStyleSheet()['Heading1']

        self.normal = ParagraphStyle(name='Normal')
        self.normalright = ParagraphStyle(
            'Normal-Right',
            parent=self.normal, alignment=2)
        self.text = ParagraphStyle(
            name='Text',
            parent=self.normal, spaceBefore=6)
        self.heading1 = ParagraphStyle(
            'Heading1',
            parent=self.normal,
            fontName=self.org_heading.fontName,
            fontSize=14, leading=18,
            spaceBefore=12, spaceAfter=6)
        self.heading2 = ParagraphStyle(
            'Heading2', parent=self.normal,
            fontName=self.org_heading.fontName,
            spaceBefore=6, spaceAfter=2)

        self.table_style = [
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # left align all cells
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # valign top all cells
            ('TOPPADDING', (0, 0), (-1, -1), 1),  # reduce top and bottom
            # padding (default is 3)
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (0, -1), 0)  # right align last row
        ]

    def render(self, bill, outfile):
        """
        render a bill as PDF in to a byte file-like output.
        """
        story = []

        story.append(Spacer(1, 2 * cm))
        self.render_addresses(bill, story)
        story.append(Spacer(1, 3 * cm))
        self.render_header(bill, story)
        story.append(Spacer(1, 0.5 * cm))
        self.render_bill_items(bill, story)
        self.render_vat(bill, story)
        story.append(Spacer(1, 0.5 * cm))

        # public notes
        if bill.public_notes:
            story.append(Paragraph(bill.public_notes, self.text))

        self.render_payments(bill, story)

        # payment notice
        url = BillingConfig.duedate_notice_url()
        if url:
            text = _('The billed amount is due for payment according to ' + 'the due date notice found here:')
            story.append(Paragraph(
                f'{text} <link href="{url}">{url}</link>.',
                self.text))

        self.render_payslip(bill, story)

        # build the pdf document
        # setting title and author prevents "anonymous" display
        # in certain pdf viewers (eg firefox)
        doc = SimpleDocTemplate(
            outfile,
            title='',
            author='',
            bottomMargin=self.bottom_margin)

        doc.build(
            story,
            onFirstPage=self.draw_payslip,
            onLaterPages=self.draw_payslip)

    def render_addresses(self, bill, story):
        """
        render table with addresses
        """
        addr = Config.organisation_address()
        org_address = Paragraph(
            '<br/>'.join(
                [addr['name'],
                 '%s %s' % (addr['street'], addr['number']),
                 '%s %s' % (addr['zip'], addr['city'])]),
            self.normal)
        memb = bill.member
        memb_address = Paragraph(
            '<br/>'.join([
                '%s %s' % (
                    memb.first_name,
                    memb.last_name),
                memb.addr_street,
                '%s %s' % (
                    memb.addr_zipcode,
                    memb.addr_location)]),
            self.normal)

        address_table = Table(
            [[org_address, memb_address]],
            style=self.table_style)
        story.append(address_table)

    def render_header(self, bill, story):
        """
        render title and billing period
        """
        # table with title and date
        title = Paragraph('%s %d' % (_('Bill'), bill.id), self.heading1)
        date = Paragraph(self.date_format(bill.bill_date), self.normalright)
        title_table = Table([(title, date)], style=self.table_style)
        story.append(title_table)

        # billing period
        period = Paragraph(
            '%s %s - %s' % (
                _('Period'),
                self.date_format(bill.business_year.start_date),
                self.date_format(bill.business_year.end_date)),
            self.normal)
        story.append(period)

    def render_bill_items(self, bill, story):
        """
        render the list of items on the bill.
        """
        lines = []
        for item in bill.ordered_items:
            lines.append((
                Paragraph(str(item), self.normal),
                Paragraph('%10.2f' % item.amount, self.normalright)))
        lines.append((
            Paragraph('<b>Total</b>', self.normal),
            Paragraph('<b>%10.2f</b>' % bill.amount, self.normalright)))

        bill_table = Table(lines, (None, 2 * cm), style=self.table_style)
        story.append(bill_table)

    def render_vat(self, bill, story):
        """
        render VAT amount, rate and number
        """
        if bill.vat_amount == 0.0:
            return

        settings = Settings.objects.first()

        story.append(
            Paragraph(
                "%s %.1f%% (%.2f)<br/>%s %s" % (
                    _("Including VAT of"),
                    bill.vat_rate * 100,
                    bill.vat_amount,
                    _("VAT Number:"),
                    settings.vat_number)
            )
        )

    def render_payments(self, bill, story):
        """
        render list of payments.
        """
        if bill.payments.all():
            story.append(Paragraph('<b>%s %s</b>' % (
                _('Payments per'),
                self.date_format(datetime.date.today())), self.heading2))

            lines = []
            sum = 0.0
            for payment in bill.payments.all():
                lines.append((
                    self.date_format(payment.paid_date),
                    payment.type,
                    Paragraph('%10.2f' % payment.amount, self.normalright)))
                sum += payment.amount

            lines.append((
                Paragraph(_('Total payments'), self.normal),
                '',
                Paragraph('%10.2f' % sum, self.normalright)))

            if sum < bill.amount:
                lines.append((
                    Paragraph(_('Amount open yet'), self.normal),
                    '',
                    Paragraph(
                        '<b>%10.2f</b>' % (bill.amount - sum),
                        self.normalright)))

            payments_table = Table(
                lines, (4 * cm, None, 2 * cm),
                style=self.table_style)

            story.append(payments_table)

            if sum >= bill.amount:
                story.append(Paragraph(_('Bill paid completely'), self.normal))

    def render_payslip(self, bill, story):
        """
        render payslip part with QR-Code
        the payslip is produced into a reporlab
        drawing, which is actually rendered by
        the page render function draw_payslip.
        """
        settings = Settings.objects.first()
        addr = Config.organisation_address()

        payment_type = settings.default_paymenttype
        if is_qr_iban(payment_type.iban):
            qr_svg = get_qrbill_svg(bill, payment_type)
            svg_element = etree.fromstring(qr_svg)

            renderer = SvgRenderer("")

            # save payslip drawing and
            # offset bottom margin
            self.qrpayslip_drawing = renderer.render(svg_element)
            self.bottom_margin = self.qrpayslip_drawing.height
        else:
            self.qrpayslip_drawing = None
            self.bottom_margin = 2 * cm

            story.append(Spacer(1, 2 * cm))

            # if no qr payslip, display account info for payment
            story.append(
                Paragraph(
                    _('Please pay specifying bill number to:'),
                    self.text))
            story.append(
                Paragraph(
                    '%s<br/>%s<br/>' % (
                        payment_type.iban,
                        payment_type.name),
                    self.text))
            story.append(
                Paragraph(
                    '%s<br/>%s, %s %s' % (
                        _('in favor of'),
                        addr['name'],
                        addr['zip'],
                        addr['city']),
                    self.text))

    def draw_payslip(self, canvas, document):
        """
        page draw function for drawing the payslip
        at the bottom of the page.
        the payslip drawing has been produced by
        the render_payslip method.
        """
        if self.qrpayslip_drawing is None:
            return

        # draw payslip at the bottom of the page without borders
        canvas.saveState()
        self.qrpayslip_drawing.drawOn(canvas, 0, 0)
        canvas.restoreState()

    def date_format(self, date):
        fmt = get_format('SHORT_DATE_FORMAT')
        return format(date, fmt)
