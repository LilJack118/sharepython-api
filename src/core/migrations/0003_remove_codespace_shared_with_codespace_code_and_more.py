# Generated by Django 4.1.4 on 2022-12-22 17:53

import core.models.codespace
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_codespace'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='codespace',
            name='shared_with',
        ),
        migrations.AddField(
            model_name='codespace',
            name='code',
            field=models.TextField(default=core.models.codespace.get_default_code_value, verbose_name='code'),
        ),
        migrations.AlterField(
            model_name='codespace',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime.now, editable=False, verbose_name='date created'),
        ),
        migrations.AlterField(
            model_name='codespace',
            name='name',
            field=models.CharField(default=core.models.codespace.get_default_name, max_length=255, verbose_name='name'),
        ),
    ]
