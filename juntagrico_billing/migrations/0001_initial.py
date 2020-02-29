# Generated by Django 2.2.6 on 2020-02-27 20:19

from django.db import migrations, models
import django.db.models.deletion
import juntagrico.entity


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('juntagrico', '0019_auto_20191127_1012'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exported', models.BooleanField(default=False, verbose_name='exported')),
                ('bill_date', models.DateField(blank=True, null=True, verbose_name='Billing date')),
                ('ref_number', models.CharField(max_length=30, unique=True, verbose_name='Reference number')),
                ('amount', models.FloatField(verbose_name='Amount')),
                ('paid', models.BooleanField(default=False, verbose_name='bezahlt')),
                ('public_notes', models.TextField(blank=True, null=True, verbose_name='Notes visible to Mitglieder')),
                ('private_notes', models.TextField(blank=True, null=True, verbose_name='Notes not visible to Mitglieder')),
                ('billable', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bills', to='juntagrico.Billable', verbose_name='Billable object')),
            ],
            options={
                'verbose_name': 'Bill',
                'verbose_name_plural': 'Bills',
            },
            bases=(models.Model, juntagrico.entity.OldHolder),
        ),
        migrations.CreateModel(
            name='BusinessYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(unique=True, verbose_name='start date')),
                ('name', models.CharField(blank='True', max_length=20, null=True, unique=True, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Business Year',
                'verbose_name_plural': 'Business Years',
            },
            bases=(models.Model, juntagrico.entity.OldHolder),
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('debtor_account', models.CharField(max_length=10, verbose_name='Debitor-Konto')),
            ],
            options={
                'verbose_name_plural': 'Settings',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionTypeAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.CharField(max_length=100, verbose_name='Konto')),
                ('subscriptiontype', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptiontype_account', to='juntagrico.SubscriptionType')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paid_date', models.DateField(blank=True, null=True, verbose_name='Paid date')),
                ('amount', models.FloatField(verbose_name='Amount number')),
                ('private_notes', models.TextField(blank=True, null=True, verbose_name='Notes not visible to Mitglieder')),
                ('bill', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='juntagrico_billing.Bill', verbose_name='Bill')),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payment',
            },
            bases=(models.Model, juntagrico.entity.OldHolder),
        ),
        migrations.CreateModel(
            name='MemberAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.CharField(max_length=100, verbose_name='Konto')),
                ('member', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='member_account', to='juntagrico.Member')),
            ],
        ),
        migrations.CreateModel(
            name='ExtraSubscriptionCategoryAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.CharField(max_length=100, verbose_name='Konto')),
                ('extrasubcategory', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='extrasub_account', to='juntagrico.ExtraSubscriptionCategory')),
            ],
        ),
        migrations.AddField(
            model_name='bill',
            name='business_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bills', to='juntagrico_billing.BusinessYear', verbose_name='Business Year'),
        ),
    ]