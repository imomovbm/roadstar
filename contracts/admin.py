from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ContractNew, ContractContext, ContractItem,
    ActivityLog, Agreement, AgreementContext
)

# ===================
# HELPER FUNCTIONS & ACTIONS
# ===================

def boolean_icon(value):
    """Show a colored dot for boolean values (green=Yes, red=No)."""
    return format_html('<span style="color: {};">●</span>', 'green' if value else 'red')

@admin.action(description="Mark selected contracts as done")
def make_done_deal(modeladmin, request, queryset):
    """Bulk mark contracts as done_deal=True."""
    updated = queryset.update(done_deal=True)
    modeladmin.message_user(request, f"{updated} contract(s) marked as done.")

# ===================
# INLINES FOR RELATED MODELS
# ===================

class ContractItemInline(admin.TabularInline):
    model = ContractItem
    extra = 0  # No extra blank lines

class AdditionalAgreementInline(admin.TabularInline):
    model = Agreement
    extra = 0
    can_delete = False  # Prevent inline deletion (optional)

class ContractContextInline(admin.TabularInline):
    model = ContractContext
    extra = 0
    fields = ("paragraph_number", "key", "value", "paragraph_text", "deleted")
    readonly_fields = ("paragraph_number", "key", "value", "paragraph_text")
    can_delete = False  # Prevent inline deletion (optional)

# ===================
# MAIN ADMIN CLASSES
# ===================

@admin.register(ContractNew)
class ContractNewAdmin(admin.ModelAdmin):
    """Admin interface for ContractNew (main contracts table)."""
    save_on_top = True
    list_filter = ("is_public", "done_deal", "canceled", "deleted", "partner")
    search_fields = ("code", "author__username", "partner__department_name")
    inlines = [ContractItemInline, AdditionalAgreementInline, ContractContextInline]
    autocomplete_fields = ["author", "partner", "client_company", "client_person"]
    readonly_fields = ["paragraph_numbers"]
    actions = [make_done_deal]

    # Custom boolean icon for "is_public"
    def is_public_icon(self, obj):
        return boolean_icon(obj.is_public)
    is_public_icon.short_description = 'Is Public'
    is_public_icon.admin_order_field = 'is_public'

    # Display columns in the admin list
    list_display = (
        "id", "code", "is_public_icon", "summ", "author", "partner", 
        "done_deal", "deleted", "canceled", "client_company", "client_person"
    )

@admin.register(ContractContext)
class ContractContextAdmin(admin.ModelAdmin):
    """Admin for customized contract paragraphs/subparagraphs."""
    list_display = ("id", "contract", "paragraph_number", "key", "value", "paragraph_text", "deleted")
    search_fields = ("contract__code", "paragraph_number", "paragraph_text")
    list_filter = ("deleted", "key")
    autocomplete_fields = ["contract"]

@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    """Admin for additional agreements on contracts."""
    list_display = ("id", "contract", "deleted", "created_date")
    search_fields = ("contract__code", "paragraph_number", "paragraph_text")
    list_filter = ("deleted",)
    autocomplete_fields = ["contract"]

@admin.register(AgreementContext)
class AgreementContextAdmin(admin.ModelAdmin):
    """Admin for additional agreements on contracts."""
    list_display = ("id", "agreement_num","paragraph_number", "paragraph_text", "deleted")
    search_fields = ("agreement__id", "paragraph_number", "paragraph_text")
    list_filter = ("deleted",)
    autocomplete_fields = ["agreement_num"]

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for event logging."""
    list_display = ('event', 'author', 'content_type', 'object_id', 'created_at')
    search_fields = ('author__username',)
    list_filter = ('event', 'content_type')

class ContractItemAdmin(admin.ModelAdmin):
    """Admin for contract items (products/services in a contract)."""
    list_display = ("id", "contract_link", "item", "cost", "amount", "deleted")
    search_fields = ("contract__code", "item__item_name")
    list_filter = ("deleted",)
    autocomplete_fields = ["contract", "item"]

    def contract_link(self, obj):
        url = f"/admin/contracts/contractnew/{obj.contract.id}/change/"
        return format_html(f'<a href="{url}">{obj.contract.code}</a>')
    contract_link.short_description = "Contract"

# If you want ContractItem in main admin sidebar (not just inline), register separately:
admin.site.register(ContractItem, ContractItemAdmin)
