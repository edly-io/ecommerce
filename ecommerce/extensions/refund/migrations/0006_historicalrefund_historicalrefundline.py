# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-02 16:18

import django.db.models.deletion
import django_extensions.db.fields
import oscar.core.utils
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0018_historicalline_historicalorder'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('refund', '0005_auto_20180628_2011'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalRefund',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('total_credit_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Total Credit (excl. tax)')),
                ('currency', models.CharField(default=oscar.core.utils.get_default_currency, max_length=12, verbose_name='Currency')),
                ('status', models.CharField(choices=[(b'Open', b'Open'), (b'Denied', b'Denied'), (b'Payment Refund Error', b'Payment Refund Error'), (b'Payment Refunded', b'Payment Refunded'), (b'Revocation Error', b'Revocation Error'), (b'Complete', b'Complete')], max_length=255, verbose_name='Status')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='order.Order', verbose_name='Order')),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical refund',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalRefundLine',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('line_credit_excl_tax', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Line Credit (excl. tax)')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Quantity')),
                ('status', models.CharField(choices=[(b'Open', b'Open'), (b'Revocation Error', b'Revocation Error'), (b'Denied', b'Denied'), (b'Complete', b'Complete')], max_length=255, verbose_name='Status')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('order_line', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='order.Line', verbose_name='Order Line')),
                ('refund', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='refund.Refund', verbose_name='Refund')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical refund line',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
