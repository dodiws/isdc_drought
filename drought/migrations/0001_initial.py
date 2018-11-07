# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HistoryDrought',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('ogc_fid', models.IntegerField(null=True, blank=True)),
                ('min', models.FloatField(null=True, blank=True)),
                ('mean', models.FloatField(null=True, blank=True)),
                ('max', models.FloatField(null=True, blank=True)),
                ('std', models.FloatField(null=True, blank=True)),
                ('sum', models.FloatField(null=True, blank=True)),
                ('count', models.FloatField(null=True, blank=True)),
                ('basin_id', models.FloatField(null=True, blank=True)),
                ('agg_code', models.CharField(max_length=50, blank=True)),
                ('woy', models.CharField(max_length=50, blank=True)),
            ],
            options={
                'db_table': 'history_drought',
                'managed': True,
            },
        ),
    ]
