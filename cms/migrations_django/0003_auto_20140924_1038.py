# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_auto_20140816_1918'),
    ]

    operations = [
        migrations.AddField(
            model_name='cmsplugin',
            name='depth',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cmsplugin',
            name='numchild',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cmsplugin',
            name='path',
            field=models.CharField(default='', unique=True, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='page',
            name='depth',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='page',
            name='numchild',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='page',
            name='path',
            field=models.CharField(default='', unique=True, max_length=255),
            preserve_default=False,
        ),
    ]
