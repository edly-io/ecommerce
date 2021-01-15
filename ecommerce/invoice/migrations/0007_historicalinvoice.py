# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-04-23 20:15
from __future__ import absolute_import, unicode_literals

import django.core.validators
import django.db.models.deletion
import django_extensions.db.fields
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('basket', '0011_add_email_basket_attribute_type'),
        ('order', '0017_order_partner'),
        ('core', '0054_ecommercefeatureroleassignment_enterprise_id'),
        ('invoice', '0006_auto_20180228_1057'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalInvoice',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('state', models.CharField(choices=[(b'Not Paid', 'Not Paid'), (b'Paid', 'Paid')], default=b'Not Paid', max_length=255)),
                ('number', models.CharField(blank=True, max_length=255, null=True)),
                ('type', models.CharField(blank=True, choices=[(b'Prepaid', 'Prepaid'), (b'Postpaid', 'Postpaid'), (b'Bulk purchase', 'Bulk purchase'), (b'Not applicable', 'Not applicable')], default=b'Prepaid', max_length=255, null=True)),
                ('payment_date', models.DateTimeField(blank=True, null=True)),
                ('discount_type', models.CharField(blank=True, choices=[(b'Percentage', 'Percentage'), (b'Fixed', 'Fixed')], default=b'Percentage', max_length=255, null=True)),
                ('discount_value', models.PositiveIntegerField(blank=True, null=True)),
                ('tax_deducted_source', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('basket', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='basket.Basket')),
                ('business_client', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='core.BusinessClient')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='order.Order')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical invoice',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
