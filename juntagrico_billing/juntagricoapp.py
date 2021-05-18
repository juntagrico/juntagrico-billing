from juntagrico.entity.member import Member
from juntagrico.entity.subtypes import SubscriptionType
from juntagrico.util import addons

import juntagrico_billing
from juntagrico_billing.admin import MemberAccountInline, SubscriptionTypeAccountInline
from juntagrico_billing.config import Config


def query_show_admin_menu(user):
    """
    book_keeper users should see the admin menu.
    """
    return user.has_perms('juntagrico.is_book_keeper')


addons.config.register_admin_menu('jb/billing_admin_menu.html')
addons.config.register_show_admin_menu_method(query_show_admin_menu)
addons.config.register_user_menu('jb/billing_user_menu.html')
addons.config.register_model_inline(Member, MemberAccountInline)
addons.config.register_model_inline(SubscriptionType, SubscriptionTypeAccountInline)
addons.config.register_config_class(Config)
addons.config.register_version(juntagrico_billing.name, juntagrico_billing.version)
