# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-05 00:34
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import intranet.utils.deletion


class Migration(migrations.Migration):

    dependencies = [('eighth', '0043_auto_20160926_2206')]

    operations = [
        migrations.AlterField(
            model_name='eighthsignup',
            name='user',
            field=models.ForeignKey(on_delete=intranet.utils.deletion.set_historical_user, to=settings.AUTH_USER_MODEL),),
        migrations.AlterField(
            model_name='eighthsponsor',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),),
    ]
