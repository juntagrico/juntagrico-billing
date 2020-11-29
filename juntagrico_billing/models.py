from django.db.models import signals

from juntagrico_billing.entity.bill import Payment
from juntagrico_billing.lifecycle.payment import payment_saved

# connect signals to lifecycle functions
signals.post_save.connect(payment_saved, sender=Payment)
