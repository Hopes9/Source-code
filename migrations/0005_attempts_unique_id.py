# Generated by Django 4.0.3 on 2022-09-09 10:36

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user_do_test', '0004_alter_user_answers_attempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempts',
            name='unique_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]