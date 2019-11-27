Settings
========

You can use the following settings to configure juntagrico-billing

ESR
---
  the ESR information

  default value

  .. code-block:: python

    ""

BILL_EMAILS
-----------
  Defining the different email templates

  default value

  .. code-block:: python

    {
        'b_share': 'mails/bill_share.txt',
        'b_sub': 'mails/bill_sub.txt',
        'b_esub': 'mails/bill_extrasub.txt'
    }