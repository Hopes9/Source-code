# Generated by Django 4.0.3 on 2022-10-04 23:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_do_test', '0008_attempts_step_id_alter_attempts_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user_answers',
            name='weight',
            field=models.IntegerField(default=5),
        ),
    ]
