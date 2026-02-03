from django.contrib import admin

# Register your models here.

from .models import UserProfile, Department, Client_company, Client_Person
# Register your models here.
class Client_companyAdmin(admin.ModelAdmin):
    list_display = ("id", "client_name", "tin_number", "pinfl_number_if_yatt", "phone_number", "email", "head_of_company", "verified", "created_at", "updated_at")
    search_fields = ["client_name", "tin_number", "pinfl_number_if_yatt", "phone_number", "email", "head_of_company"]

class Client_PersonAdmin(admin.ModelAdmin):
    list_display = ("id", "client_name", "pinfl", "passport_number", "phone_number", "email", "head_of_company", "verified", "created_at", "updated_at")
    search_fields = ["client_name", "pinfl", "passport_number", "phone_number", "email", "head_of_company"]

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "department_name")
    search_fields = ["department_name"]


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "role", "department", "user")


admin.site.register(Department, DepartmentAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Client_company, Client_companyAdmin)
admin.site.register(Client_Person, Client_PersonAdmin)