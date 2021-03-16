from juntagrico.config import _get_setting, _get_setting_with_key


class Config:
    """
    billing specific settings.
    Config class is registered with juntagrico.addons.
    """
    esr = _get_setting('ESR', '')

    bill_emails = _get_setting_with_key(
        'BILL_EMAILS',
        {
            'b_share': 'mails/bill_share.txt',
            'b_sub': 'mails/bill_sub.txt',
            'b_esub': 'mails/bill_extrasub.txt'
        }
    )

    bills_usermenu = _get_setting('BILLS_USERMENU', False)

    duedate_notice_url = _get_setting('DUEDATE_NOTICE_URL', '')
