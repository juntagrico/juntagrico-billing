from django.template.loader import get_template
from django.utils.translation import gettext as _

from juntagrico.config import Config
from juntagrico.mailer import EmailSender, organisation_subject
from juntagrico.management.commands.mailtexts import get_server


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
        organisation_subject(_('Rechnung {0}').format(Config.vocabulary('share'))),
        content,
    ).send_to(member.email)


def send_bill_sub(bill, subscription, start, end, member):
    plaintext = get_template('mails/bill_sub.txt')
    d = {
        'member': member,
        'bill': bill,
        'sub': subscription,
        'start': start,
        'end': end,
        'serverurl': get_server()
    }
    content = plaintext.render(d)

    content = plaintext.render(d)
    EmailSender.get_sender(
        organisation_subject(_('Rechnung {0}').format(Config.vocabulary('subscription'))),
        content,
    ).send_to(member.email)


def send_bill_extrasub(bill, extrasub, start, end, member):
    plaintext = get_template('mails/bill_extrasub.txt')
    d = {
        'member': member,
        'bill': bill,
        'extrasub': extrasub,
        'start': start,
        'end': end,
        'serverurl': get_server()
    }
    content = plaintext.render(d)

    content = plaintext.render(d)
    EmailSender.get_sender(
        organisation_subject(_('Rechnung Extra-Abo')),
        content,
    ).send_to(member.email)
