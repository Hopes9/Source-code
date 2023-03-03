# Generated by Django 4.0.3 on 2022-09-09 10:56

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user_do_test', '0005_attempts_unique_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attempts',
            name='unique_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]