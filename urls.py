from django.urls import path
from .views import Get_information_about_test, Start_test, Get_int_question, Finish_question, Start, Get_result, Get_advanced_result, Edit_bals_user_answer

urlpatterns = [
    path("<str:pk>", Get_information_about_test.as_view(), name="test_for_user"),
    path("<str:session_id>/questions/<int:number>", Start_test.as_view()),
    path("<str:session_id>/questions/get_questions", Get_int_question.as_view()),
    path("<str:pk>/start", Start.as_view()),
    path("<str:session_id>/finish", Finish_question.as_view()),
    path("result/<str:link>", Get_result.as_view()),
    path("result_advanced/<str:user_id>/<int:test_id>/<int:attempt>", Get_advanced_result.as_view()),
    path("edit_balls_for_questions/<str:attempt>", Edit_bals_user_answer.as_view())
]

