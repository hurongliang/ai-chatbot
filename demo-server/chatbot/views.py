from django.http import HttpResponse
import json
from chatbot.models import MilvusModel
import traceback
from services import LogService
from apscheduler.schedulers.background import BackgroundScheduler


model = MilvusModel()


scheduler = BackgroundScheduler()


@scheduler.scheduled_job('interval', seconds=60)
def fit_collection():
    model.fit()


scheduler.start()


def train(req):
    try:
        body = req.body.decode('utf-8')
        data = json.loads(body)
        LogService.debug('train data: %s', data)
        questions = data['questions']
        answers = data['answers']
        botid = model.train(questions, answers)
        return HttpResponse(botid)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(str(e), status=500)


def clean(req):
    body = req.body.decode('utf-8')
    data = json.loads(body)
    LogService.debug('clean param: %s', data)
    model.clean(data['botid'])
    return HttpResponse()


def infer(req):
    try:
        body = req.body.decode('utf-8')
        data = json.loads(body)
        LogService.debug('infer data %s', data)
        q = data['q']
        botid = data['botid']

        a = model.infer(q, botid)
        return HttpResponse(a)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(str(e), status=500)


def save(req):
    try:
        body = req.body.decode('utf-8')
        data = json.loads(body)
        LogService.debug('save data %s', data)
        botid = data['botid']
        title = data['title']
        a = model.save(botid, title)
        return HttpResponse(a)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(str(e), status=500)


def load(req):
    try:
        botid = req.GET.get('botid')
        LogService.info('get by session %s ', botid)
        a = model.get(botid)
        return HttpResponse(a)
    except Exception as e:
        traceback.print_exc()
        return HttpResponse(str(e), status=500)





