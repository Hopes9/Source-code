import datetime
import uuid
from random import shuffle

from apscheduler.schedulers.background import BackgroundScheduler
from django.http import QueryDict
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from test_work.models import List_tests, List_question
from test_work.permissions import IsTeacherUser
from user_do_test.func import finish_test, get_status, update_balls, find_by_key, avto_finish_test
from user_do_test.models import User_answers, Attempts, Statistic_answer
from user_do_test.serializers import About_test, Post_answers, Get_next_question, \
    Start_add_attemtp, Result_user

scheduler = BackgroundScheduler()
scheduler.start()


@permission_classes([IsAuthenticated])
class Get_information_about_test(APIView):
    def get(self, request, pk):
        queryset = List_tests.objects.filter(secret_link=pk).first()
        if queryset is None:
            return Response({"detail": "Test no found"}, status=status.HTTP_404_NOT_FOUND)
        if not queryset.open:
            return Response({"detail": "Тест закрыт"}, status=status.HTTP_204_NO_CONTENT)
        if queryset.random_questions is None:
            enter_data = {
                "count_question": List_question.objects.filter(id_test_id=queryset.id, delete=False).count(),
                "name": queryset.name,
                "creator": queryset.id_creator.get_full_name(),
                "subject": queryset.subject.id,
            }
        else:
            enter_data = {
                "count_question": str(queryset.random_questions),
                "name": queryset.name,
                "creator": queryset.id_creator.get_full_name(),
                "subject": queryset.subject.id,
            }
        serializer_for_queryset = About_test(instance=queryset, data=enter_data)
        serializer_for_queryset.is_valid(raise_exception=True)
        serializer_for_queryset.save()

        query_quest = Attempts.objects.filter(id_user_id=request.user.id, start=True).last()
        data = {}
        if query_quest is not None:
            data.update(serializer_for_queryset.data)
            data.update({"session_id": query_quest.unique_id})
            data.update({"test_id": query_quest.id_test.secret_link})
        else:
            data = serializer_for_queryset.data
            data.update({"session_id": None})

        return Response(data, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
class Get_int_question(APIView):
    def get(self, request, session_id):
        query_quest = Attempts.objects.filter(unique_id=session_id)
        if len(query_quest) == 0:
            return Response({"detail": "Нужно начать тест"}, status=status.HTTP_409_CONFLICT)

        query_quest_attempt = query_quest.first()
        if query_quest_attempt.finish:
            return Response({"detail": "Сессия закрыта"}, status=status.HTTP_409_CONFLICT)

        queryset_test = query_quest_attempt.id_test
        list_questions = List_question.objects.filter(id_test_id=queryset_test.id, delete=False).order_by("id")
        list_answers = User_answers.objects.filter(attempt_id=query_quest_attempt.id)
        list_question = []
        data = {"perhaps_skip_question": queryset_test.perhaps_skip_question,
                "time_start": query_quest_attempt.time_start,
                "time": queryset_test.time_work, "count_questions": len(query_quest_attempt.list_questions),
                "questions": list_question}
        count = 0
        val1 = list_answers.values()
        val = list_questions.values("id", "question", "type", "answers", "image")
        for i in query_quest_attempt.list_questions:
            user_answer = find_by_key(val1, "id_question_id", i)
            df = {}
            if user_answer is not None:
                if queryset_test.perhaps_skip_question:
                    di = find_by_key(val, "id", i)
                    if int(di["type"]) != 5:
                        upd = di["answers"]
                        shuffle(upd)
                        df.update(di)
                        df.update({"answers": upd})
                    else:
                        upd = di["answers"]
                        shuffle(upd["keys"])
                        shuffle(upd["answers"])
                        df.update(di)
                    df.update({"user_answer": user_answer["answer"]})
                    list_question.append(df)
                count += 1
            else:
                di = find_by_key(val, "id", i)
                if int(di["type"]) != 5:
                    upd = di["answers"]
                    shuffle(upd)
                    df.update(di)
                    df.update({"answers": upd})
                else:
                    upd = di["answers"]
                    shuffle(upd["keys"])
                    shuffle(upd["answers"])
                    df.update(di)
                    df.update({"answers": upd})

                df.update({"user_answer": None})

                list_question.append(df)
                if not queryset_test.perhaps_skip_question:
                    break

        data.update({"answers": count})
        return Response(data, status=status.HTTP_200_OK)


class Start(APIView):
    def post(self, request, pk):
        user_id = request.user.id
        row = request.data
        test_user = List_tests.objects.get(secret_link=pk)
        if test_user is None:
            return Response({"detail": "Такого теста нету"}, status=status.HTTP_409_CONFLICT)

        id_test = test_user.id
        chek_close_test = Attempts.objects.filter(id_user_id=user_id, start=True, id_test=test_user.id)
        if len(chek_close_test) == 0:
            if not test_user.open:
                return Response({"test": "Тест закрыт"}, status=status.HTTP_200_OK)

            list_true_answers = List_question.objects.filter(id_test_id=id_test, delete=False).order_by(
                "id").values_list(
                "id", "id_true_answer")
            if test_user.random_questions is None:
                list_true_answers = list(list_true_answers.values_list("id", flat=True))
            else:
                list_true_answers = list(list_true_answers.values_list("id", flat=True))
                shuffle(list_true_answers)
                list_true_answers = list_true_answers[:test_user.random_questions]
            if test_user.random_list_questions:
                shuffle(list_true_answers)
            if len(list_true_answers) == 0:
                return Response({"detail": "В тесте нет вопросов"}, status=status.HTTP_409_CONFLICT)
            user_stat = Attempts.objects.filter(id_test_id=id_test, id_user=user_id).last()
            unique_id_ = uuid.uuid4()
            time_start = timezone.now()
            enter_data_attemtp = {
                "id_user": user_id,
                "start": True,
                "time_start": time_start,
                "list_questions": list_true_answers,
                "status_test": 2,
                "unique_id": unique_id_
            }
            if row.get("step_id") is not None:
                enter_data_attemtp.update(step_id=row.get("step_id"))
            if test_user.time_work is not None:
                scheduler.add_job(avto_finish_test, 'date', [request, unique_id_],
                                  run_date=datetime.datetime.now() + datetime.timedelta(
                                      seconds=(test_user.time_work * 60) + 1))
            else:
                scheduler.add_job(avto_finish_test, 'date', [request, unique_id_],
                                  run_date=datetime.datetime.now() + datetime.timedelta(days=1))
            if user_stat is not None:
                if (test_user.attempt is None) or (user_stat.attempt < test_user.attempt):
                    attempt = user_stat.attempt + 1
                    enter_data_attemtp.update(attempt=attempt)
                    enter_data_attemtp.update(id_test=user_stat.id_test_id)
                    serialize = Start_add_attemtp(data=enter_data_attemtp)
                    serialize.is_valid(raise_exception=True)
                    serialize.save()
                    return Response(
                        {"detail": "Тест начался, есть попытки", "time": time_start, "session_id": unique_id_},
                        status=status.HTTP_200_OK)
                else:
                    return Response({"detail": "У вас нет попыток"}, status=status.HTTP_404_NOT_FOUND)
            else:
                enter_data_attemtp.update(attempt=1)
                enter_data_attemtp.update(id_test=id_test)

                serialize = Start_add_attemtp(data=enter_data_attemtp)
                serialize.is_valid(raise_exception=True)
                serialize.save()
                return Response({"test": "Тест начался", "time": time_start, "session_id": unique_id_},
                                status=status.HTTP_200_OK)
        else:
            chek_close_test = chek_close_test.first()
            time_start = chek_close_test.time_start
            if test_user.attempt is not None:
                if test_user.time_work is not None:
                    time_work_user = datetime.timedelta(minutes=test_user.time_work)
                    time_now = timezone.now()
                    if time_now > (time_start + time_work_user):
                        finish_test(request.user.id, session_id=chek_close_test.unique_id)
                        return Response({"detail": "У теста закончилось время, тест закрыт"},
                                        status=status.HTTP_409_CONFLICT)
                    else:
                        return Response(
                            {"detail": "Вы уже начали тест, для завершения теста выполните все вопросы или "
                                       "завершите тест заранее, если время того тест закончится, "
                                       "то тот "
                                       "тест "
                                       "закроется автоматически"}, status=status.HTTP_409_CONFLICT)
            finish_test(request.user.id, session_id=chek_close_test.unique_id)
            return Response({"detail": "Есть не закрытый тест, тест закрыт, начните заново"},
                            status=status.HTTP_409_CONFLICT)


@permission_classes([IsAuthenticated])
class Start_test(APIView):
    def patch(self, request, number, session_id):
        attempt = Attempts.objects.filter(unique_id=session_id, start=True)
        if len(attempt):
            queryset = List_tests.objects.filter(id=attempt.first().id_test.id)
            if len(queryset):
                if not queryset.first().open:
                    return Response({"detail": "Тест закрыт"}, status=status.HTTP_409_CONFLICT)
                else:
                    test_user = queryset.first()
                    id_test = test_user.id
                    user_id = request.user.id
                    if len(attempt) != 0:
                        attrm = attempt.last()
                        if test_user.time_work is not None:
                            time_work_user = datetime.timedelta(minutes=test_user.time_work)
                            time_now = timezone.now()
                            if time_now > (attrm.time_start + time_work_user):
                                finish_test(request.user.id, session_id)
                                return Response({"detail": "Время закончилось"}, status=status.HTTP_409_CONFLICT)
                        data = request.data
                        if isinstance(data, QueryDict):
                            enter_data = {
                                "id_test": int(id_test),
                                "id_question": int(number),
                                "user_id": user_id,
                                "attempt": attrm.id,
                                # "weight": List_question.objects.filter(id=int(number)).first().weight
                            }
                            data._mutable = True
                            data.update(enter_data)
                        else:
                            return Response({"detail": "Нужно передать answer"}, status=status.HTTP_409_CONFLICT)
                        if number in attrm.list_questions:
                            answer = User_answers.objects.filter(user_id_id=user_id, id_question=number,
                                                                 id_test_id=int(id_test), attempt=attrm.id)
                            if len(answer) == 0 or test_user.perhaps_skip_question:
                                serializer = Post_answers(answer.first(), data=data)
                                serializer.is_valid(raise_exception=True)
                                serializer.save()
                                list_answer = User_answers.objects.filter(user_id_id=user_id, id_test_id=id_test,
                                                                          attempt=attrm.id).order_by("id_question")
                                list_answer_list = []
                                for i in attrm.list_questions:
                                    list_answer_list.append(i)
                                for g in list_answer.values_list("id_question", flat=True):
                                    list_answer_list.remove(g)
                                if len(list_answer_list) == 0:
                                    return Response({"questions": "all answered", "answer": data["answer"]},
                                                    status=status.HTTP_200_OK)
                                else:
                                    queryset = List_question.objects.filter(id_test_id=id_test, id=list_answer_list[0])
                                    serializer_for_queryset = Get_next_question(instance=queryset, many=True)
                                    return Response(serializer_for_queryset.data[0], status=status.HTTP_200_OK)
                            else:
                                return Response({"detail": "Ответ уже записан"}, status=status.HTTP_409_CONFLICT)
                        else:
                            return Response({"detail": "Этот тест не имеет этого вопроса"},
                                            status=status.HTTP_409_CONFLICT)
                    else:
                        return Response({"detail": "Тест не начат"}, status=status.HTTP_409_CONFLICT)
        else:
            return Response({"detail": "error 404"}, status=status.HTTP_409_CONFLICT)


@permission_classes([IsAuthenticated])
class Finish_question(APIView):
    def get(self, request, session_id):
        att = Attempts.objects.get(unique_id=session_id)
        if att is not None:
            return finish_test(request.user.id, att.unique_id)
        else:
            return Response({"detail": "Не правильный session_id"})


class Get_result(APIView):
    def get(self, request, link):
        get_id = Statistic_answer.objects.get(link=link)
        if get_id is not None:
            attempt = Attempts.objects.filter(id=get_id.attempt_id).prefetch_related("id__test_id").select_related(
                "id_test__subject")
            attempt = attempt.first()
            data = {
                "subject": attempt.id_test.subject.name,
                "test": attempt.id_test.name,
                "attempt": attempt.attempt,
                "true_answers": attempt.count_bals,
                "max_bals": attempt.max_bals,
                "time": attempt.time_finish - attempt.time_start,
            }
            data = data | {"one_char": attempt.id_test.one_char, "marks": attempt.id_test.marks}
            data = data | {"status": get_status(attempt.id_test, (attempt.count_bals / attempt.max_bals) * 100)}
            return Response(data)
        return Response({"detail": "Не найдена попытка"}, status=status.HTTP_409_CONFLICT)


@permission_classes([IsAuthenticated, IsTeacherUser])
class Get_advanced_result(APIView):
    def get(self, request, user_id, test_id, attempt):
        user = User.objects.get(unique_id=user_id)
        if user is None:
            return Response({"detail": "Пользователь не найден"}, status=status.HTTP_409_CONFLICT)

        test = List_tests.objects.get(id=test_id)
        if test is None:
            return Response({"detail": "Тест не найден"}, status=status.HTTP_409_CONFLICT)

        question = List_question.objects.filter(id_test=test.id)
        attempt = Attempts.objects.filter(attempt=attempt, id_test_id=test.id, id_user_id=user.id,
                                          finish=True).last()
        if attempt is None:
            return Response({"detail": "Попытки на найдены"}, status=status.HTTP_409_CONFLICT)

        user_na = User_answers.objects.filter(user_id=user.id, id_test=test.id, attempt=attempt.id)
        questions = []
        if attempt.max_bals != 0:
            stat = get_status(test, (attempt.count_bals / attempt.max_bals) * 100)
        else:
            stat = "0"
        val1 = question.values()
        val2 = user_na.values()
        for i in attempt.list_questions:
            ques = find_by_key(val1, "id", int(i))
            # ques = question.filter(id=int(i)).first()
            try:
                us = find_by_key(val2, "id_question_id", i)
                # us = user_na.filter(id_question=i).first()
                questions.append(
                    {
                        "id": ques["id"],
                        "question": ques["question"],
                        "type": int(ques["type"]),
                        "answer": ques["answers"],
                        "id_true_answer": ques["id_true_answer"],
                        "user_answer": us["answer"],
                        "weight": us["weight"],
                        "max_weight": ques["weight"],
                        "image": str(ques["image"])
                    }
                )
            except:
                questions.append(
                    {
                        "id": ques["id"],
                        "question": ques["question"],
                        "type": int(ques["type"]),
                        "answer": ques["answers"],
                        "id_true_answer": ques["id_true_answer"],
                        "user_answer": [],
                        "weight": None,
                        "max_weight": ques["weight"],
                        "image": str(ques["image"])
                    }
                )
        data = {
            "test": {
                "id_test": attempt.id_test.id,
                "name": f"{test.subject.name} / {test.name}",
                "result": f"{attempt.count_bals}/{attempt.max_bals}",
                "attempt": attempt.attempt,
                "session_id": attempt.unique_id,
                "status_test": attempt.status_test.name,
                "time": attempt.time_finish - attempt.time_start,
                "status": stat
            },
            "name": f"{user.last_name} {user.first_name} {user.middle_name}",
            "attempt": questions
        }
        return Response(data, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated, IsTeacherUser])
class Edit_bals_user_answer(APIView):
    def patch(self, request, attempt):
        att = Attempts.objects.get(unique_id=attempt)
        if att is None:
            return Response({"detail": "Попытка не найдена"}, status=status.HTTP_409_CONFLICT)
        user_ans = User_answers.objects.filter(attempt_id=att.id)
        lj = user_ans.values_list("id_question", flat=True)
        for i in request.data:
            if i["id"] in lj:
                user_ans.filter(id_question=i["id"]).update(weight=i["weight"])
        return update_balls(att.id_user, att, user_ans)

