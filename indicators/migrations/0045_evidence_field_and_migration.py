# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def copy_evidence_from_documents(apps, schema_editor):
    Result = apps.get_model('indicators', 'Result')
    for result in Result.objects.filter(evidence__isnull=False).select_related('evidence'):
        doc = result.evidence
        # either of these fields may be NULL on the Documentation, so force to empty str
        result.evidence_name = doc.name or ''
        result.evidence_url = doc.url or ''
        result.save()


def reverse_migration(apps, schema_editor):
    """Allow the reverse migration to happen"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0044_merge_20181228_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalresult',
            name='evidence_name',
            field=models.CharField(blank=True, max_length=135),
        ),
        migrations.AddField(
            model_name='historicalresult',
            name='evidence_url',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='result',
            name='evidence_name',
            field=models.CharField(blank=True, max_length=135),
        ),
        migrations.AddField(
            model_name='result',
            name='evidence_url',
            field=models.CharField(blank=True, max_length=255),
        ),

        # data migration
        migrations.RunPython(copy_evidence_from_documents, reverse_code=reverse_migration),
    ]
