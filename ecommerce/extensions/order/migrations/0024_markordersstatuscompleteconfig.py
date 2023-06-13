# Generated by Django 2.2.14 on 2020-07-20 11:09

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0023_auto_20200305_1448'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarkOrdersStatusCompleteConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('txt_file', models.FileField(help_text='It expect that the order numbers stuck in fulfillment error state will be             provided in a txt file format one per line.', upload_to='', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['txt'])])),
                ('changed_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
    ]
