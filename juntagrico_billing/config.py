from juntagrico.config import _get_setting


class Config:
    """
    billing specific settings.
    Config class is registered with juntagrico.addons.
    """
    bills_usermenu = _get_setting('BILLS_USERMENU', False)

    duedate_notice_url = _get_setting('DUEDATE_NOTICE_URL', '')
