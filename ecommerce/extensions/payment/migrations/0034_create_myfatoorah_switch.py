# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations

from ecommerce.extensions.payment.processors.myfatoorah import MyFatoorah


def create_switch(apps, schema_editor):
    """ Create the switch that gates the MyFatoorah processor.

    Created inactive: MyFatoorah is only for tenants that have credentials, so it
    should be switched on deliberately rather than appearing everywhere on deploy.
    """
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.get_or_create(
        name=settings.PAYMENT_PROCESSOR_SWITCH_PREFIX + MyFatoorah.NAME,
        defaults={'active': False},
    )


def delete_switch(apps, schema_editor):
    Switch = apps.get_model('waffle', 'Switch')
    Switch.objects.filter(name=settings.PAYMENT_PROCESSOR_SWITCH_PREFIX + MyFatoorah.NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('payment', '0033_merge_20250114_0556'),
        ('waffle', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_switch, delete_switch)
    ]
