# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-05-26 01:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20170525_2131'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfiguration',
            name='partner',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='partner.Partner'),
        ),
        migrations.AlterUniqueTogether(
            name='siteconfiguration',
            unique_together=set([]),
        ),
    ]
