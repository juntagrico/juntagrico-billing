from juntagrico.entity.extrasubs import ExtraSubscriptionCategory
from juntagrico.entity.member import Member
from juntagrico.entity.subtypes import SubscriptionType
from juntagrico.util import addons

from juntagrico_billing.admin import MemberAccountInline, SubscriptionTypeAccountInline, \
    ExtraSubscriptionCategoryAccountInline
from juntagrico_billing.config import Config

addons.config.register_admin_menu('jb/billing_admin_menu.html')
addons.config.register_user_menu('jb/billing_user_menu.html')
addons.config.register_model_inline(Member, MemberAccountInline)
addons.config.register_model_inline(SubscriptionType, SubscriptionTypeAccountInline)
addons.config.register_model_inline(ExtraSubscriptionCategory, ExtraSubscriptionCategoryAccountInline)
addons.config.register_config_class(Config)
