import collections
import secrets
import string

import requests
from django.utils import timezone
from rest_framework.response import Response

from PollHub.settings import LXP_SERVER
from test_work.models import List_question
from user_do_test.models import User_answers, Attempts, Statistic_answer
from user_do_test.serializers import Finish_question_sereliz, Add_statistik


def avto_finish_test(request, uid):
    return finish_test(request.user.id, uid)


def get_status(test, precent):
    if test.one_char:
        if precent >= int(test.marks):
            return "Сдал"
        else:
            return "Не сдал"
    else:
        if test.marks["excellent"][1] >= precent >= test.marks["excellent"][0]:
            return "5"
        elif test.marks["good"][1] >= precent >= test.marks["good"][0]:
            return "4"
        elif test.marks["bad"][1] >= precent >= test.marks["bad"][0]:
            return "3"
        else:
            return "2"


def get_boolean_get_status(test, precent, status):
    stat = get_status(test, precent)
    if status == 3:
        return "pending"
    if test.one_char:
        if stat == "Сдал":
            return "done"
        else:
            return "failed"
    else:
        if int(stat) >= 3:
            return "done"
        else:
            return "failed"


def request_to_lxp(attempt, link, status):
    url = f"{LXP_SERVER}/api/v2/poll-hub/results"
    present = (attempt.count_bals / attempt.max_bals) * 100
    headers = {
        'Authorization': 'Bearer WYIKO6KHJ8OsuThvT5zPWgyqj81AYQOP&bs9h5UeF12MbQni_wcRa.EGejS9Vei'
    }
    payload = {
        "user_id": attempt.id_user.user_id_lxp,
        "step_id": attempt.step_id,
        "status": get_boolean_get_status(attempt.id_test, present, status),
        "percent": present
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    return response


def find_by_key(iterable, key, value):
    for index, dict_ in enumerate(iterable):
        if key in dict_ and dict_[key] == value:
            return dict_


def find_all_by_key(iterable, key, value):
    dicts = []
    for index, dict_ in enumerate(iterable):
        if key in dict_ and dict_[key] == value:
            dicts.append(dict_)
    return dicts


def finish_test(user_id, session_id):
    chek_close_test = Attempts.objects.filter(unique_id=session_id, start=True)
    if len(chek_close_test) != 0:
        attempt = chek_close_test.last()
        user_ans = User_answers.objects.filter(user_id_id=user_id, id_test_id=attempt.id_test,
                                               attempt=attempt.id).order_by("id_question")
        list_test = List_question.objects.filter(id_test_id=attempt.id_test, delete=False).order_by("id")

        list_test = list_test.values("id", "type", "id_true_answer", "weight")
        list_true_answers_one_answer = find_all_by_key(list_test, "type", "1")
        list_true_answers_many_answers = find_all_by_key(list_test, "type", "2")
        list_true_answers_text = find_all_by_key(list_test, "type", "3")
        list_true_answers_sequence = find_all_by_key(list_test, "type", "4")
        list_true_comparison = find_all_by_key(list_test, "type", "5")

        # max_bals = sum(list_test.values_list("weight", flat=True))
        max_bals = 0
        for i in attempt.list_questions:
            max_bals += find_by_key(list_test, "id", i)["weight"]

        count_true_answers = 0
        count_weight_answers = 0

        values_use = list(user_ans.values())

        if len(user_ans) != 0:
            # one_answer
            for i in list_true_answers_one_answer:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    print(i)
                    if collections.Counter(i["id_true_answer"]) == collections.Counter(ans["answer"]):
                        count_true_answers += 1
                        count_weight_answers += i["weight"]
                        User_answers.objects.filter(attempt=attempt.id, id_question=i["id"]).update(weight=i["weight"])
                except Exception as e:
                    print(e)
            print(count_true_answers, count_weight_answers, "one_answer")

        # text
        # if len(list_true_answers_text) != 0:
        #     for i in list_true_answers_text:
        #         try:
        #             ans = user_ans.get(id_question=i["id"])
        #             ans.weight = find_by_key(list_true_answers_text, "id", i["id"])["weight"]
        #             ans.save()
        #         except Exception as e:
        #             print(e)

        # many_answers
        if len(list_true_answers_many_answers) != 0:
            for i in list_true_answers_many_answers:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if len(ans["answer"]) == len(i["id_true_answer"]):
                        if collections.Counter(ans["answer"]) == collections.Counter(i["id_true_answer"]):
                            count_true_answers += 1
                            count_weight_answers += i["weight"]
                            User_answers.objects.filter(attempt=attempt.id, id_question=i["id"]).update(
                                weight=i["weight"])
                except Exception as e:
                    print(e)
            print(count_true_answers, count_weight_answers, "many_answers")
        # sequence
        if len(list_true_answers_sequence) != 0:
            for i in list_true_answers_sequence:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if len(ans["answer"]) == len(i["id_true_answer"]):
                        True_ans = False
                        counter = 0
                        for g in i["id_true_answer"]:
                            if str(g) == str(ans["answer"][counter]):
                                counter += 1
                                True_ans = True
                            else:
                                True_ans = False
                                break
                        if True_ans:
                            count_true_answers += 1
                            count_weight_answers += i["weight"]
                            User_answers.objects.filter(attempt=attempt.id, id_question=i["id"]).update(
                                weight=i["weight"])
                except Exception as e:
                    print(e)
            print(count_true_answers, count_weight_answers, "sequence")

        # comparison
        if len(list_true_comparison) != 0:
            for i in list_true_comparison:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if len(i["id_true_answer"]) == len(ans["answer"]):
                        counter = 0
                        True_ans = False
                        for a in ans["answer"]:
                            if collections.Counter(i["id_true_answer"][counter]) == collections.Counter(a):
                                True_ans = True
                            else:
                                True_ans = False
                                break
                            counter += 1
                        if True_ans:
                            count_true_answers += 1
                            count_weight_answers += i["weight"]
                            User_answers.objects.filter(attempt=attempt.id, id_question=i["id"]).update(
                                weight=i["weight"])
                except Exception as e:
                    print(e)
        print(count_true_answers, count_weight_answers, "comparison")
        status_test = get_stat(list_true_answers_text)
        enter_data = {
            "id_test": attempt.id_test.id,
            "id_user": attempt.id_user.id,
            "status_test": status_test,
            "true_answers": count_true_answers,
            "count_questions": len(attempt.list_questions),
            "time_finish": timezone.now(),
            "start": False,
            "finish": True,
            "count_bals": count_weight_answers,
            "max_bals": max_bals,
        }
        print(enter_data)
        serializer = Finish_question_sereliz(instance=attempt, data=enter_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        enter_data_ = {
            "link": get_secret_key_(),
            "attempt": attempt.id
        }
        serializer = Add_statistik(data=enter_data_)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = {
            "attempt": attempt.attempt,
            "true_answers": attempt.count_bals,
            "max_bals": attempt.max_bals,
            "time": attempt.time_finish - attempt.time_start,
            "link": serializer.data["link"],
        }
        if attempt.step_id is not None:
            lxp = request_to_lxp(attempt, serializer.data["link"], status_test)
            data = data | {"lxp_status_code": lxp}
        data = data | {"one_char": attempt.id_test.one_char, "marks": attempt.id_test.marks}
        data = data | {"status": get_status(attempt.id_test, (attempt.count_bals / attempt.max_bals) * 100)}
        return Response(data)
    else:
        chek_close_test = Attempts.objects.filter(unique_id=session_id)
        attempt = chek_close_test.last()
        data = {
            "attempt": attempt.attempt,
            "true_answers": attempt.count_bals,
            "count_questions": attempt.count_questions,
            "time": attempt.time_finish - attempt.time_start,
            "detail": "All test close"
        }
        data = data | {"one_char": attempt.id_test.one_char, "marks": attempt.id_test.marks}
        return Response(data)


def update_balls(user_id, att, user_ans):
    if att is not None:
        attempt = att
        user_ans = User_answers.objects.filter(user_id_id=user_id, id_test_id=attempt.id_test,
                                               attempt=attempt.id).order_by("id_question")
        list_test = List_question.objects.filter(id_test_id=attempt.id_test, delete=False).order_by("id")

        list_test = list_test.values("id", "type", "id_true_answer", "weight")
        list_true_answers_one_answer = find_all_by_key(list_test, "type", "1")
        list_true_answers_many_answers = find_all_by_key(list_test, "type", "2")
        list_true_answers_text = find_all_by_key(list_test, "type", "3")
        list_true_comparison = find_all_by_key(list_test, "type", "5")
        list_true_answers_sequence = find_all_by_key(list_test, "type", "4")

        max_bals = 0
        for i in attempt.list_questions:
            max_bals += find_by_key(list_test, "id", i)["weight"]

        count_true_answers = 0
        count_weight_answers = 0

        values_use = list(user_ans.values())

        if len(list_true_answers_one_answer) != 0:
            # one_answer
            for i in list_true_answers_one_answer:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if collections.Counter(i["id_true_answer"]) == collections.Counter(ans["answer"]):
                        count_true_answers += 1
                    print(ans["weight"])
                    count_weight_answers += ans["weight"]
                except Exception as e:
                    print(e)
            print(count_true_answers, count_weight_answers)
            # text
        if len(list_true_answers_text) != 0:
            for i in list_true_answers_text:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    count_weight_answers += ans["weight"]
                except Exception as e:
                    print(e)

        # many_answers
        if len(list_true_answers_many_answers) != 0:
            try:
                for i in list_true_answers_many_answers:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if len(ans["answer"]) == len(i["id_true_answer"]):
                        if collections.Counter(ans["answer"]) == collections.Counter(i["id_true_answer"]):
                            count_true_answers += 1
                    count_weight_answers += ans["weight"]
            except Exception as e:
                print(e)
            print(count_true_answers, count_weight_answers)

        # sequence
        if len(list_true_answers_sequence) != 0:
            for i in list_true_answers_sequence:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if len(ans["answer"]) == len(i["id_true_answer"]):
                        True_ans = False
                        counter = 0
                        for g in i["id_true_answer"]:
                            if str(g) == str(ans["answer"][counter]):
                                counter += 1
                                True_ans = True
                            else:
                                True_ans = False
                                break
                        if True_ans:
                            count_true_answers += 1
                    count_weight_answers += ans["weight"]
                except Exception as e:
                    print(e)
            print(count_true_answers, count_weight_answers, "sequence")

        # comparison
        if len(list_true_comparison) != 0:
            for i in list_true_comparison:
                try:
                    ans = find_by_key(values_use, "id_question_id", i["id"])
                    if len(i["id_true_answer"]) == len(ans["answer"]):
                        counter = 0
                        True_ans = False
                        for a in ans["answer"]:
                            if collections.Counter(i["id_true_answer"][counter]) == collections.Counter(a):
                                True_ans = True
                            else:
                                True_ans = False
                                break
                        counter += 1
                        if True_ans:
                            count_true_answers += 1
                    count_weight_answers += ans["weight"]
                except Exception as e:
                    print(e)

        enter_data = {
            "id_test": attempt.id_test.id,
            "id_user": attempt.id_user.id,
            "status_test": get_stat(list_true_answers_text),
            "true_answers": count_true_answers,
            "count_questions": len(attempt.list_questions),
            "count_bals": count_weight_answers,
            "max_bals": max_bals,
        }
        serializer = Finish_question_sereliz(instance=attempt, data=enter_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "attempt": attempt.attempt,
            "count_balls": attempt.count_bals,
            "max_balls": attempt.max_bals,
            "time": attempt.time_finish - attempt.time_start,
        })


def get_secret_key_():
    rand_string = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    if len(Statistic_answer.objects.filter(link=rand_string)) > 0:
        return get_secret_key_()
    return rand_string


def get_stat(list_true_answers_text):
    if len(list_true_answers_text) == 0:
        return 1
    else:
        return 3
