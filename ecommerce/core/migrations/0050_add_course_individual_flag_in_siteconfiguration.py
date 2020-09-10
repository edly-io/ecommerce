# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-09-10 09:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_auto_20200414_0843'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='enable_course_individual_payments',
            field=models.BooleanField(default=True, help_text='Flag to check if site wise course individual payments are enabled', verbose_name='Enable Course Individual Payments'),
        ),
    ]
