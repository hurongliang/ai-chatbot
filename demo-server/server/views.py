from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render


def index(request):
    return render(request, 'server/index.html')


def check(request):
    return HttpResponse("It works")
