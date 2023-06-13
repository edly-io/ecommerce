# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-10 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0024_auto_20191212_1630'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='card_type',
            field=models.CharField(blank=True, choices=[('american_express', 'American Express'), ('discover', 'Discover'), ('mastercard', 'MasterCard'), ('visa', 'Visa')], max_length=255, null=True),
        ),
    ]
