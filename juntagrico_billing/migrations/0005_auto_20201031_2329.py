# Generated by Django 3.1.1 on 2020-10-31 22:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('juntagrico_billing', '0004_auto_20201031_1823'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='payment',
            options={'verbose_name': 'Zahlung', 'verbose_name_plural': 'Zahlungen'},
        ),
        migrations.AlterModelOptions(
            name='paymenttype',
            options={'verbose_name': 'Zahlungstyp', 'verbose_name_plural': 'Zahlungstypen'},
        ),
        migrations.AddField(
            model_name='settings',
            name='default_paymenttype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='juntagrico_billing.paymenttype'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='juntagrico_billing.paymenttype', verbose_name='Zahlungstyp'),
        ),
    ]
