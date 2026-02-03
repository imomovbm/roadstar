from django.contrib.auth.models import User
from django.db import models
from users.models import Client_company, Client_Person, Department
from products.models import Mahsulot
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
    
from django.contrib.postgres.fields import ArrayField


def default_paragraph_numbers():
    return [2, 3, 4, 5]
    
class ContractNew(models.Model):
    code = models.CharField(max_length=20, blank=True, null=True)
    summ = models.BigIntegerField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    partner =  models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.CharField(max_length=50, blank=True, null=True)
    created_date = models.DateField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    public_token = models.CharField(max_length=36, unique=True, blank=True, null=True)
    done_deal = models.BooleanField(default=False)
    canceled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    paragraph_numbers = ArrayField(
        base_field=models.IntegerField(),
        default=default_paragraph_numbers,
        blank=True
    )
    
    # Optional foreign keys to either one of the client types
    client_company = models.ForeignKey(
        Client_company, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts_as_company'
    )
    client_person = models.ForeignKey(
        Client_Person, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contracts_as_person'
    )

    def __str__(self):
        return f"{self.code} raqamli yangi shartnoma"

    def save(self, *args, **kwargs):
        if self.is_public and not self.public_token:
            self.public_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def get_client(self):
        return self.client_company or self.client_person
    
    def get_client_name(self):
        if self.client_company:
            return self.client_company.client_name
        elif self.client_person:
            return self.client_person.client_name
        return None
    
    def get_phone_number(self):
        if self.client_company:
            return self.client_company.phone_number
        elif self.client_person:
            return self.client_person.phone_number
        return None
    
    def get_tin_number(self):
        if self.client_company:
            return self.client_company.tin_number
        elif self.client_person:
            return self.client_person.tin_number
        return None
    
    def get_head_of_company(self):
        if self.client_company:
            return self.client_company.head_of_company
        elif self.client_person:
            return self.client_person.head_of_company
        return None


class ContractContext(models.Model):
    KEY_CHOICES = [
    ('header', 'header'),
    ('text', 'text'),
    ]
    contract = models.ForeignKey(ContractNew, on_delete=models.CASCADE, related_name="contexts")
    paragraph_number = models.IntegerField(blank=True, null=True)
    key = models.CharField(blank=True, null=True, choices=KEY_CHOICES)
    value = models.IntegerField(blank=True, null=True)
    paragraph_text = models.TextField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.contract.pk} - Paragraflar {self.paragraph_number}"

class Agreement(models.Model):
    contract = models.ForeignKey(ContractNew, on_delete=models.CASCADE, related_name="agreement")
    code = models.IntegerField(blank=True, null=True)
    created_date = models.DateField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.pk}"

class AgreementContext(models.Model):
    agreement_num = models.ForeignKey(Agreement, on_delete=models.CASCADE, related_name="agreement_contexts")
    paragraph_number = models.CharField(max_length=5,blank=True, null=True)
    paragraph_text = models.TextField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.agreement_num} - Paragraflar {self.paragraph_number}:{self.paragraph_text}"


class ContractItem(models.Model):
    contract = models.ForeignKey(ContractNew, on_delete=models.CASCADE, related_name="contract_items")
    item = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    cost = models.BigIntegerField(blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item.item_name} in {self.contract.pk}"


class ActivityLog(models.Model):
    EVENT_CHOICES = [
        ('create', 'yaratildi'),
        ('edit', 'o\'zgartirildi'),
        ('delete', 'o\'chirildi'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.CharField(max_length=10, choices=EVENT_CHOICES)
    # For "what object was changed":
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content_object} {self.event} by {self.author.username}"