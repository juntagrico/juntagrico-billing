# juntagrico-billing


[![juntagrico-ci](https://github.com/juntagrico/juntagrico-billing/actions/workflows/juntagrico-ci.yml/badge.svg?branch=main&event=push)](https://github.com/juntagrico/juntagrico-billing/actions/workflows/juntagrico-ci.yml)
[![Maintainability](https://qlty.sh/gh/juntagrico/projects/juntagrico-billing/maintainability.svg)](https://qlty.sh/gh/juntagrico/projects/juntagrico-billing)
[![Code Coverage](https://qlty.sh/gh/juntagrico/projects/juntagrico-billing/coverage.svg)](https://qlty.sh/gh/juntagrico/projects/juntagrico-billing)
[![image](https://img.shields.io/github/last-commit/juntagrico/juntagrico-billing.svg)](https://github.com/juntagrico/juntagrico-billing)
[![image](https://img.shields.io/github/commit-activity/y/juntagrico/juntagrico-billing)](https://github.com/juntagrico/juntagrico-billing)

This is an extension for juntagrico. You can find more information about juntagrico here
(https://github.com/juntagrico/juntagrico).

It provides the following features for juntagrico:
* creating managing bills (invoices) for juntagrico subscriptions
* display of bills as HTML or PDF
* support for swiss qr bill with reference number
* manage payments for bills
* reading camt.054 payment files (in connection with qr bills and refnumer)
* bookkeeping export covering bills and payments

## Installation

Install juntagrico-billing via pip
`pip install juntagrico-billing`

or add it to your main django projects `requirements.txt`:
`juntagrico-billing`

You may also install from github source (or add it to `requirements.txt`):
`pip install git+https://github.com/juntagrico/juntagrico-billing.git`

In your `juntagrico.settings.py` add `juntagrico_billing` somewhere **above** `juntagrico`:
```python
INSTALLED_APPS = (
    'juntagrico_billing',
    'juntagrico',
    ...
```

In your urls.py you also need to add the new pattern:
```python
urlpatterns = [
    ...
    path('',include('juntagrico_billing.urls')),
]
```

As the billing app introduces its own database tables, you need to apply migrations after installing.
Execute `python manage.py migrate` in your main django project.

## Configuration

Set these in your `settings.py` to modify `juntagrico-billing`

### BILLS_USERMENU
  Set to True to add "bills" to the user menu.

  default value: False

### DUEDATE_NOTICE_URL
  Set the url of a page that explains the due date policy of your bills, if you have any.

  default value: ''

## Create settings object

`juntagrico-billing` uses a singleton `Settings` object to store some setting.
You need to create this settings object once in django admin.

- Log in to juntagrico and go to the admin UI at `https://<my juntagrico site>/admin`.
- You should see in admin a new section for juntagrico_billing
  ![grafik](https://user-images.githubusercontent.com/3380098/110239635-419b4600-7f48-11eb-8fb7-afed31983a2d.png)
- Add a new Settings object
  
  <img width="607" height="341" alt="image" src="https://github.com/user-attachments/assets/4d04be43-8828-4357-8167-ec222a6cefa0" />

  
- You need to specify a debtors account, just specify any digit code (e.g. `1100`)
- If needed, specify a surcharge account. Surcharges may be added by optional apps like `juntagrico-contribution` to a subscription. When created by `juntagrico-contribution` this would be an income account used for subscription.
- A default paymenttype is mandatory too. You may create one directly from the settings dialog:
  ![grafik](https://user-images.githubusercontent.com/3380098/110239772-f9c8ee80-7f48-11eb-8866-7844d234e971.png)
- The paymenttype for balancing bills must be specified too. It is used for bookings representing the difference to the normal amount when overpaying a bill.
- VAT number (optional), used to show the vat number on PDF bills.
- VAT percent (mandatory), may be 0 if no vat is applicable.
- Save your settings object. There must be only one settings object.

## Create a business year

Billing is done on the base of a business-year. A business-year denotes the time period for creating bills.
Usually this will correspond to a calendar year (1.1 - 31.1 of a year). It is possible to use different timespans though.
Business-years should be consecutive.

Business years are managed in django admin UI. 

- Log in to `/admin` and create a new businessyear object
  ![grafik](https://user-images.githubusercontent.com/3380098/110240002-20d3f000-7f4a-11eb-8118-aebd351228b4.png)


## Billing

Billing is based on the activation and deactivation dates of subscriptions (and extrasubscriptions) in juntagrico.
At any time you may create all needed invoices (bills) for a certain business-year.

In juntagrico you should see the `Bills and Bookkeeping` Menu, if you are assigned bookkeeping rights.

Go to `Bills` and choose the desired business-year.
Switch to the `Generate bills` tab. The amount of pending bills for the businessyear should then be displayed.
This may take some time depending on the number of subscriptions and members in your system.
![grafik](https://user-images.githubusercontent.com/3380098/110240325-ae640f80-7f4b-11eb-8288-4f2ec16811f9.png)

Pressing the `Generate` button will create these bills.
They may be viewed afterwards on the `all` tab of the bills list.
![grafik](https://user-images.githubusercontent.com/3380098/110240404-0a2e9880-7f4c-11eb-9a5b-3ad92af46c50.png)

### Modifying or adding bills

There are two modes to view an existing bill object:
- admin view of the bill. click on the first column of a bill row to open the bill in django admin.
- user view of the bill. click on the last columdn of a bill row to open the bill as the user will see it.

If a bill created via `Generate` is incorrect, proceed as follows:
- delete the bill in the django admin UI
- correct the subscription settings
  - in most cases this will involve adjusting the activation or deactivation date of the subscription / extrasubscription
- re-create the bill by going to the `Generate bills` tab on the `Bills` list.
  - if you only modified one subscription, it should say `1 pending bill`
  - click on `Generate` to re-create the bill based on the modified settings

The same procedure applies if a new subscription or subscription part (extrasubscription) is added after bills for a business-year have been generated.
If there already is a bill for the same member and you want the additional parts to appear on the same bill, you may delete the existing bill and regenerate it like described above.
Deleting a bill is only possible if there are no payments on it.
If you add parts without deleting an existing bill, then a new bill will be added for the member.

### Adding custom items to a bill

In addition to subscription and extrasubscription parts, a bill may also contain custom items.
Custom items may be used for stuff like
- correcting overpaid bills
- adding special credit for a certain member (work instead of paying)
- adding additional contributions (solidarity contributions)

For each kind of custom item you need to define a custom Bill item type in django admin:
![grafik](https://user-images.githubusercontent.com/3380098/110240808-f126e700-7f4d-11eb-9e73-35f43138a48e.png)

You need to specify a description and a booking account for the custom item type.

You may then add custom item types on a bill in the django admin view of the bill:
![grafik](https://user-images.githubusercontent.com/3380098/110240939-8c1fc100-7f4e-11eb-8e62-45393ddd1600.png)

## Bookings Export
The bookings that are derived from bills and payments can be exported into an accounting package.
The accounting export page features a date range that filters the bookings to be exported.
There are 2 ways to export bookings:
### Download Excel
Downloads an excel sheet containing all bookings. This may serve as base for importing into an accounting software.
### Export to Bexio
Writes the bookings via API into the Bexio (https://bexio.com) accounting package. 
Identification of the Bexio account and authorisation is provided by an authentication token (a long text string) that needs to be pasted in the corresponding field. Such a token may be generated via the Bexio developer page at https://developer.bexio.com. 
The export performs a synchronisation between juntagrico bookings and manual bookings in Bexio. Export may be started multiple times for the same period, only the differences are written to the API. Depending on the number of existing manual bookings in Bexio, the export action may take quite a long time.
