from django.template.loader import get_template
from django.utils.translation import gettext as _

from juntagrico.config import Config
from juntagrico.mailer import send_mail
from juntagrico.management.commands.mailtexts import get_server


def send_bill_share(bill, share, member):
    plaintext = get_template(Config.emails('b_share'))
    d = {
        'member': member,
        'bill': bill,
        'share': share,
        'serverurl': get_server()
    }
    content = plaintext.render(d)
    send_mail(_('{0} - Rechnung {1}').format(Config.organisation_name(), Config.vocabulary('share')),
              content, Config.info_email(), [member.email])


def send_bill_sub(bill, subscription, start, end, member):
    plaintext = get_template(Config.emails('b_sub'))
    d = {
        'member': member,
        'bill': bill,
        'sub': subscription,
        'start': start,
        'end': end,
        'serverurl': get_server()
    }
    content = plaintext.render(d)
    send_mail(_('{0} - Rechnung {1}').format(Config.organisation_name(), Config.vocabulary('subscription')),
              content, Config.info_email(), [member.email])


def send_bill_extrasub(bill, extrasub, start, end, member):
    plaintext = get_template(Config.emails('b_esub'))
    d = {
        'member': member,
        'bill': bill,
        'extrasub': extrasub,
        'start': start,
        'end': end,
        'serverurl': get_server()
    }
    content = plaintext.render(d)
    send_mail(_('{0} - Rechnung Extra-Abo').format(Config.organisation_name()),
              content, Config.info_email(), [member.email])
