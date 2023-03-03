from rest_framework import serializers
from test_work.models import List_tests
from test_work.models import List_question
from user_do_test.models import User_answers, Attempts, Statistic_answer


class About_test(serializers.ModelSerializer):
    subject = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = List_tests
        depth = 1
        exclude = ["id", "id_creator", "secret_link", "date_create"]
        # fields = "__all__"


class Get_next_question(serializers.ModelSerializer):
    class Meta:
        model = List_question
        # fields = "__all__"
        exclude = ["id_true_answer", "id_test", "weight", "delete"]


class Post_answers(serializers.ModelSerializer):
    class Meta:
        model = User_answers
        # exclude = ["id", "id_test", "user_id"]
        fields = "__all__"


class Finish_question_sereliz(serializers.ModelSerializer):
    class Meta:
        model = Attempts
        fields = "__all__"


class Start_add_attemtp(serializers.ModelSerializer):
    class Meta:
        model = Attempts
        fields = "__all__"


class Add_statistik(serializers.ModelSerializer):
    class Meta:
        model = Statistic_answer
        fields = "__all__"


class Update_answer(serializers.ModelSerializer):
    class Meta:
        model = User_answers
        fields = "__all__"


class Result_user(serializers.ModelSerializer):
    class Meta:
        model = Attempts
        fields = ["attempt", "count_bals", "max_bals", "time_start", "time_finish", "status_test"]
        depth = 1
