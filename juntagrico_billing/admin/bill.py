from juntagrico.admins import BaseAdmin


class BillAdmin(BaseAdmin):
    raw_id_fields = ['billable', 'business_year']
    list_display = ['billable', 'bill_date', 'amount', 'ref_number']