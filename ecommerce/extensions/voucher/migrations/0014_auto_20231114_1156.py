# Generated by Django 3.2.20 on 2023-11-14 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voucher', '0013_make_voucher_names_unique'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='voucher',
            options={'get_latest_by': 'date_created', 'ordering': ['-date_created'], 'verbose_name': 'Voucher', 'verbose_name_plural': 'Vouchers'},
        ),
        migrations.AlterModelOptions(
            name='voucherapplication',
            options={'ordering': ['-date_created'], 'verbose_name': 'Voucher Application', 'verbose_name_plural': 'Voucher Applications'},
        ),
        migrations.AlterModelOptions(
            name='voucherset',
            options={'get_latest_by': 'date_created', 'ordering': ['-date_created'], 'verbose_name': 'VoucherSet', 'verbose_name_plural': 'VoucherSets'},
        ),
        migrations.RemoveField(
            model_name='voucherset',
            name='offer',
        ),
        migrations.AlterField(
            model_name='historicalvoucherapplication',
            name='date_created',
            field=models.DateTimeField(blank=True, db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='name',
            field=models.CharField(help_text='This will be shown in the checkout and basket once the voucher is entered', max_length=128, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='voucherapplication',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='voucherset',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='voucherset',
            name='name',
            field=models.CharField(max_length=100, unique=True, verbose_name='Name'),
        ),
    ]