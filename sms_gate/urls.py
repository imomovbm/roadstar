from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = "sms_gate"

urlpatterns = [
    path("", views.index, name="index"),
    path("send", views.send_sms, name="send_sms"),
    path("doi", views.doi, name="doi"),
] 