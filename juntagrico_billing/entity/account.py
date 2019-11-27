from django.db import models
from juntagrico.entity.extrasubs import ExtraSubscriptionCategory
from juntagrico.entity.member import Member
from juntagrico.entity.subtypes import SubscriptionType


class MemberAccount(models.Model):
    """
    Account number for members.
    Implemented as inline admin record on member.
    """

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='member_account')
    account = models.CharField('Konto', max_length=100)

    def __str__(self):
        return self.member.get_name()


class SubscriptionTypeAccount(models.Model):
    """
    Account number for type of subscription.
    Implemented as inline admin record on SubscriptionType.
    """
    subscriptiontype = models.OneToOneField(SubscriptionType, on_delete=models.CASCADE,
                                            related_name='subscriptiontype_account')
    account = models.CharField('Konto', max_length=100)


class ExtraSubscriptionCategoryAccount(models.Model):
    """
    Account number for extra subscriptions. Is located on extra subscription category.
    Implemented as inline admin record on ExtraSubscriptionCategory.
    """
    extrasubcategory = models.OneToOneField(ExtraSubscriptionCategory, on_delete=models.CASCADE,
                                            related_name="extrasub_account")
    account = models.CharField('Konto', max_length=100)
