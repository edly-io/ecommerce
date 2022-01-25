# Generated by Django 2.2.12 on 2020-04-07 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0063_auto_20200117_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfiguration',
            name='enable_enrollment_codes',
            field=models.BooleanField(blank=True, default=False, help_text='Enable the creation of enrollment codes.', verbose_name='Enable enrollment codes'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='enable_microfrontend_for_basket_page',
            field=models.BooleanField(blank=True, default=False, help_text='Use the microfrontend implementation of the basket page instead of the server-side template', verbose_name='Enable Microfrontend for Basket Page'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='enable_partial_program',
            field=models.BooleanField(blank=True, default=False, help_text='Enable the application of program offers to remaining unenrolled or unverified courses', verbose_name='Enable Partial Program Offer'),
        ),
        migrations.AlterField(
            model_name='siteconfiguration',
            name='send_refund_notifications',
            field=models.BooleanField(blank=True, default=False, verbose_name='Send refund email notification'),
        ),
    ]