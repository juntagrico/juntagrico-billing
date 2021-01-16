from django.db.models import signals

from juntagrico_billing.entity.bill import BillItem
from juntagrico_billing.entity.payment import Payment
from juntagrico_billing.lifecycle.payment import payment_saved
from juntagrico_billing.lifecycle.billitem import billitem_saved

# connect signals to lifecycle functions
signals.post_save.connect(payment_saved, sender=Payment)
signals.post_save.connect(billitem_saved, sender=BillItem)
