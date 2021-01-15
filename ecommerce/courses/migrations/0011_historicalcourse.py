# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-02 16:18
from __future__ import absolute_import, unicode_literals

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0002_alter_domain_unique'),
        ('partner', '0014_historicalstockrecord'),
        ('courses', '0010_migrate_partner_data_to_courses'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalCourse',
            fields=[
                ('id', models.CharField(db_index=True, max_length=255, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('verification_deadline', models.DateTimeField(blank=True, help_text='Last date/time on which verification for this product can be submitted.', null=True)),
                ('created', models.DateTimeField(blank=True, editable=False, null=True)),
                ('modified', models.DateTimeField(blank=True, editable=False, null=True)),
                ('thumbnail_url', models.URLField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('partner', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='partner.Partner')),
                ('site', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='sites.Site', verbose_name='Site')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical course',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
