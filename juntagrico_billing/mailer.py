from django.template.loader import get_template
from django.utils.translation import gettext as _
from juntagrico.config import Config
from juntagrico.mailer import EmailSender, organisation_subject, base_dict
from juntagrico.management.commands.mailtexts import get_server

from juntagrico_billing.entity.settings import Settings


def send_bill_share(bill, share, member):
    plaintext = get_template('mails/bill_share.txt')
    d = {
        'member': member,
        'bill': bill,
        'share': share,
        'serverurl': get_server()
    }
    content = plaintext.render(d)
    EmailSender.get_sender(
        organisation_subject(_('Bill {0}').format(Config.vocabulary('share'))),
        content,
    ).send_to(member.email)


def send_bill_notification(bill):
    # prepare variables that are passed to
    # template using locals()
    settings = Settings.objects.first()
    payment_type = settings.default_paymenttype
    business_year = bill.business_year
    member = bill.member
    start_date = business_year.start_date
    end_date = business_year.end_date

    plaintext = get_template('mails/bill_notification.txt')
    content = plaintext.render(base_dict(locals()))
    subject = organisation_subject(_('{0} Bill').format(Config.vocabulary('subscription')))

    EmailSender.get_sender(content, subject).send_to(member.email)
