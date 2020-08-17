from juntagrico.admins import BaseAdmin


class BusinessYearAdmin(BaseAdmin):
    list_display = ['name', 'start_date']
