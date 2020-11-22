def payment_saved(instance, **kwargs):
    """
    called on save of a payment
    check if full amount of bill reached
    and mark the bill as paid
    """
    bill = instance.bill
    total_paid = sum((p.amount for p in bill.payments.all()))
    if total_paid >= bill.amount:
        bill.paid = True
        bill.save()
