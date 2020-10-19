from django.urls import path
from chatbot import views

urlpatterns = [
    path('train/', views.train),
    path('clean/', views.clean),
    path('infer/', views.infer),
    path('save/', views.save),
    path('load/', views.load)
]
