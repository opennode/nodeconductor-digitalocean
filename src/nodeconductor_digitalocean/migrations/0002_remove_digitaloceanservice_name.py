# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_digitalocean', '0002_auto_20170210_1345'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='digitaloceanservice',
            name='name',
        ),
    ]
