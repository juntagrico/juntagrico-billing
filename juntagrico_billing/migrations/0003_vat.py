# Generated by Django 4.0.3 on 2023-01-10 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('juntagrico_billing', '0002_bill_published'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='vat_rate',
            field=models.FloatField(default=0.0, verbose_name='MWST Satz'),
        ),
        migrations.AddField(
            model_name='billitem',
            name='vat_amount',
            field=models.FloatField(default=0.0, verbose_name='MWST Betrag'),
        ),
        migrations.AddField(
            model_name='settings',
            name='vat_number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='MWST Nummer'),
        ),
        migrations.AddField(
            model_name='settings',
            name='vat_percent',
            field=models.FloatField(default=0.0, verbose_name='MWST Prozent'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='published',
            field=models.BooleanField(default=False, verbose_name='Veröffentlicht'),
        ),
    ]
