# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-12-12 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0023_auto_20191126_2153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='card_type',
            field=models.CharField(blank=True, choices=[('discover', 'Discover'), ('visa', 'Visa'), ('mastercard', 'MasterCard'), ('american_express', 'American Express')], max_length=255, null=True),
        ),
    ]
