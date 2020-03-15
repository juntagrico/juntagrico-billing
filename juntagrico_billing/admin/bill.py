from juntagrico.admins import BaseAdmin
from juntagrico_billing.admin.payment_inline import PaymentInline
from juntagrico_billing.entity.bill import Bill


class BillAdmin(BaseAdmin):
    raw_id_fields = ['business_year']
    list_display = ['business_year', 'billable_inst', 'bill_date', 'amount']
    inlines = [PaymentInline, ]

    def billable_inst(self, bill):
        """
        Get the concrete polymorphic instance.
        Otherwise the admin list display only shows the abstract base class (Billable).
        """
        return bill.billable.get_real_instance()

    billable_inst.short_description = Bill._meta.get_field('billable').verbose_name
    
