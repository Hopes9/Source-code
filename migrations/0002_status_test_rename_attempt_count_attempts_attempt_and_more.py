# Generated by Django 4.0.3 on 2022-08-31 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('test_work', '0002_remove_list_tests_creator_and_more'),
        ('user_do_test', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Status_test',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.TextField(default='Закрыт')),
            ],
        ),
        migrations.RenameField(
            model_name='attempts',
            old_name='attempt_count',
            new_name='attempt',
        ),
        migrations.RemoveField(
            model_name='attempts',
            name='id_stat',
        ),
        migrations.RemoveField(
            model_name='user_answers',
            name='id_number',
        ),
        migrations.AddField(
            model_name='attempts',
            name='count_bals',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='attempts',
            name='id_test',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='test_work.list_tests'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attempts',
            name='max_bals',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user_answers',
            name='id_question',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='test_work.list_question'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user_answers',
            name='weight',
            field=models.IntegerField(default=1),
        ),
        migrations.DeleteModel(
            name='User_statistik',
        ),
        migrations.AddField(
            model_name='attempts',
            name='status_test',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='user_do_test.status_test'),
            preserve_default=False,
        ),
    ]