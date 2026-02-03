from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = "products"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", login_required(views.create_product), name="create"), 
    path("save/", login_required(views.save_product), name="save"), 
    path("edit/<int:pk>/", login_required(views.edit_product), name="edit"),  
  
    ]