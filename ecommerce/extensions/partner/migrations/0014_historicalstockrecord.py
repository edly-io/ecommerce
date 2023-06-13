# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-02 16:18

import django.db.models.deletion
import oscar.core.utils
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0039_historicalproduct_historicalproductattributevalue'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('partner', '0013_partner_default_site'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalStockRecord',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('partner_sku', models.CharField(max_length=128, verbose_name='Partner SKU')),
                ('price_currency', models.CharField(default=oscar.core.utils.get_default_currency, max_length=12, verbose_name='Currency')),
                ('price_excl_tax', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Price (excl. tax)')),
                ('price_retail', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Price (retail)')),
                ('cost_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Cost Price')),
                ('num_in_stock', models.PositiveIntegerField(blank=True, null=True, verbose_name='Number in stock')),
                ('num_allocated', models.IntegerField(blank=True, null=True, verbose_name='Number allocated')),
                ('low_stock_threshold', models.PositiveIntegerField(blank=True, null=True, verbose_name='Low Stock Threshold')),
                ('date_created', models.DateTimeField(blank=True, editable=False, verbose_name='Date created')),
                ('date_updated', models.DateTimeField(blank=True, db_index=True, editable=False, verbose_name='Date updated')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('partner', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='partner.Partner', verbose_name='Partner')),
                ('product', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='catalogue.Product', verbose_name='Product')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical Stock record',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
