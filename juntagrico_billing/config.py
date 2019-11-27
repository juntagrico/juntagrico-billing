from django.conf import settings


class Config:
    def __init__(self):
        pass

    @staticmethod
    def esr():
        if hasattr(settings, 'ESR'):
            return settings.ESR
        return ''

    @staticmethod
    def bill_emails(key):
        if hasattr(settings, 'BILL_EMAILS'):
            if key in settings.BILL_EMAILS:
                return settings.BILL_EMAILS[key]
        return {'b_share': 'mails/bill_share.txt',
                'b_sub': 'mails/bill_sub.txt',
                'b_esub': 'mails/bill_extrasub.txt'
                }[key]
