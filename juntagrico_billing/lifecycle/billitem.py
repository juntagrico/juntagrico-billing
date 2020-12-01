def billitem_saved(instance, **kwargs):
    """
    called on save of a bill-item
    adjust the total amount of the bill
    """
    bill = instance.bill
    total_amount = sum([item.amount for item in bill.items.all()])
    if bill.amount != total_amount:
        bill.amount = total_amount
        bill.save()
