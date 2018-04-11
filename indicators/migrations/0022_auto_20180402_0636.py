# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-02 13:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0021_auto_20180331_2030'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalindicator',
            name='direction_of_change',
            field=models.IntegerField(choices=[(1, b'Direction of change (not applicable)'), (2, b'Positive (+)'), (3, b'Negative (-)')], default=1, help_text=b' ', null=True, verbose_name=b'Direction of Chnage'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='direction_of_change',
            field=models.IntegerField(choices=[(1, b'Direction of change (not applicable)'), (2, b'Positive (+)'), (3, b'Negative (-)')], default=1, help_text=b' ', null=True, verbose_name=b'Direction of Chnage'),
        ),
    ]