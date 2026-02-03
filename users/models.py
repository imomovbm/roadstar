from django.contrib.auth.models import User
from django.db import models

class Department(models.Model):
    department_name = models.CharField(max_length=100, blank=True, null=True)  # Only needed for regional/subadmins
    address = models.CharField(max_length=255, blank=True, null=True)
    tin_number = models.CharField(max_length=50, unique=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_address = models.CharField(max_length=255, blank=True, null=True)
    mfo = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)  
    app_password = models.CharField(max_length=100, blank=True, null=True)
    head_of_company = models.CharField(max_length=100, blank=True, null=True)
    DEPARTMENT_CATEGORY = [
        ('1', 'Avtosalon'),
        ('2', 'Avtoehtiyot qismlari'),
    ]
    category = models.CharField(max_length=20, choices=DEPARTMENT_CATEGORY)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.department_name}"


class Client_company(models.Model): 
    client_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    tin_number = models.CharField(max_length=50, unique=True)
    pinfl_number_if_yatt = models.CharField(max_length=14, null=True, blank=True,)
    passport_series_number_if_yatt = models.CharField(max_length=10, null=True, blank=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_address = models.CharField(max_length=255, blank=True, null=True)
    mfo = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)  
    head_of_company = models.CharField(max_length=100, blank=True, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_name}"

class Client_Person(models.Model): 
    client_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    tin_number = models.CharField(max_length=50, unique=True)
    pinfl = models.CharField(max_length=50, unique=True)
    passport_number = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)  
    head_of_company = models.CharField(max_length=100, blank=True, null=True)
    verified = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.client_name}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'SuperAdmin'),
        ('regionaladmin', 'Filial'),
        ('moder', 'Moder'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} : {self.role}"
    

