# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-25 23:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0039_metricsindicator'),
    ]

    operations = [
        migrations.RunSQL("ALTER TABLE `indicators_collecteddata` ADD KEY (indicator_id)")
    ]
