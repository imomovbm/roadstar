from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = "users"

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("choose-department", views.choose_department, name="choose_department"),
    path("logout", views.logout_view, name="logout"),
    path("profile", login_required(views.user_profile), name="user_profile"),  
    path("save-profile", login_required(views.save_profile), name="save_profile"),  
    path("save-password", login_required(views.save_password), name="save_password"),  

    path("departments", login_required(views.departments), name="departments"),  
    path("departments/create/", login_required(views.create_department), name="create_department"), 
    path("departments/save/", login_required(views.save_department), name="save_department"), 
    
    path("departments/edit/<int:pk>/", login_required(views.edit_department), name="edit_department"),  
    
    # Company Routes
    path("client-company", login_required(views.client_company), name="client_company"), 
    path("client-company/create/", login_required(views.create_client_company), name="create_client_company"), 
    path("client-company/save/", views.save_client_company, name="save_client_company"),
    path("client-company/edit/<int:pk>/", views.edit_client_company, name="edit_client_company"),

    # yatt routes
    path("client-yatt/create/", login_required(views.create_client_yatt), name="create_client_yatt"), 

    #  Person Routes
    path("client-person", login_required(views.client_person), name="client_person"),
    path("client-person/create/", login_required(views.create_client_person), name="create_client_person"), 
    path("client-person/save/", views.save_client_person, name="save_client_person"),
    path("client-person/edit/<int:pk>/", views.edit_client_person, name="edit_client_person"),

    path('api/fetch-company/', views.fetch_company_data, name='fetch_company'),
    path("api/check-company/", views.check_company, name="check_company"),
    path("api/check-person/", views.check_person, name="check_person"),
    path('create-user/', views.create_user_view, name='create_user'),
] 