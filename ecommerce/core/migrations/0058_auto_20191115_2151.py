# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-11-15 21:51
from __future__ import unicode_literals

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20190920_1752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ecommercefeatureroleassignment',
            name='enterprise_id',
            field=models.UUIDField(blank=True, null=True, verbose_name='Enterprise Customer UUID'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='affiliate_cookie_name',
            field=models.CharField(blank=True, default='', help_text='Name of cookie storing affiliate data.', max_length=255, verbose_name='Affiliate Cookie Name'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='base_cookie_domain',
            field=models.CharField(blank=True, default='', help_text='Base cookie domain used to share cookies across services.', max_length=255, verbose_name='Base Cookie Domain'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='payment_support_email',
            field=models.CharField(blank=True, default='support@example.com', help_text='Contact email for payment support issues.', max_length=255, verbose_name='Payment support email'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='theme_scss_path',
            field=models.CharField(blank=True, help_text='DEPRECATED: THIS FIELD WILL BE REMOVED!', max_length=255, null=True, verbose_name='Path to custom site theme'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='utm_cookie_name',
            field=models.CharField(blank=True, default='', help_text='Name of cookie storing UTM data.', max_length=255, verbose_name='UTM Cookie Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, db_index=True, max_length=254, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
        ),
    ]
