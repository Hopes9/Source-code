import uuid

from django.db import models

from accounts.models import User
from test_work.models import List_tests, List_question


class Status_test(models.Model):
    id = models.AutoField(primary_key=True)
    CATEGORY_CHOICES = (
        (1, "Закрыт"),
        (2, "Прохождение"),
        (3, "Проверка"),
        (4, "Ошибка")
    )
    name = models.CharField(max_length=200, choices=CATEGORY_CHOICES)


class Attempts(models.Model):
    id = models.AutoField(primary_key=True, db_index=True)
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True)
    id_test = models.ForeignKey(List_tests, on_delete=models.CASCADE)
    id_user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt = models.IntegerField(default=1)

    count_bals = models.IntegerField(default=0)
    max_bals = models.IntegerField(default=0)

    true_answers = models.IntegerField(default=0)
    count_questions = models.IntegerField(default=0)
    start = models.BooleanField(default=False)
    finish = models.BooleanField(default=False)
    time_start = models.DateTimeField(null=True)
    time_finish = models.DateTimeField(null=True)
    list_questions = models.JSONField(default=dict)
    status_test = models.ForeignKey(Status_test, on_delete=models.CASCADE)
    step_id = models.IntegerField(default=None, null=True)


class User_answers(models.Model):
    id = models.AutoField(primary_key=True)
    attempt = models.ForeignKey(Attempts, on_delete=models.CASCADE, db_index=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    id_test = models.ForeignKey(List_tests, on_delete=models.CASCADE)
    id_question = models.ForeignKey(List_question, on_delete=models.CASCADE)
    answer = models.JSONField()
    comment = models.TextField(null=True)
    weight = models.IntegerField(default=0)


class Statistic_answer(models.Model):
    id = models.AutoField(primary_key=True)
    link = models.TextField()
    attempt = models.ForeignKey(Attempts, on_delete=models.CASCADE)

# python manage.py migrate --run-syncdb




