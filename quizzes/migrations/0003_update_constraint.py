# Generated by Django 2.2.11 on 2020-04-03 11:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0002_add_timing_special'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='question',
            unique_together=set(),
        ),
    ]
