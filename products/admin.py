from django.contrib import admin
from .models import Mahsulot

@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = (
        'item_name', 'code', 'cypher_code', 'measurement', 'category', 
        'default_cost', 'deleted', 'created_at', 'updated_at'
    )
    search_fields = ['item_name', 'code', 'cypher_code', 'category']
    list_filter = ['category', 'deleted', 'created_at', 'updated_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
