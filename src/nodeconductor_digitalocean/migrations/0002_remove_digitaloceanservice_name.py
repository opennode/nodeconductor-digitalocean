# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nodeconductor_digitalocean', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='digitaloceanservice',
            name='name',
        ),
    ]
