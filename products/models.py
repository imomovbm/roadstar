from django.db import models


# Create your models here.
class Mahsulot(models.Model):  
    item_name = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)
    cypher_code = models.CharField(max_length=255, blank=True, null=True)
    measurement = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=25, blank=True, null=True)
    default_cost = models.BigIntegerField(blank=True, null=True)
    deleted = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} dan" 