# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-19 18:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0020_auto_20180918_1554'),
        ('indicators', '0032_auto_20180706_1037'),
    ]

    operations = [
        migrations.CreateModel(
            name='PinnedReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Report Name')),
                ('report_type', models.CharField(max_length=32)),
                ('query_string', models.CharField(max_length=255)),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow.Program')),
                ('tola_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow.TolaUser')),
            ],
        ),
    ]
