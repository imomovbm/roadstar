from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = "contracts"

urlpatterns = [
    path("", login_required(views.index), name="index"),
    path("<int:pk>/", login_required(views.contract_detail), name="detail"),

    path("context/<int:pk>/", login_required(views.contract_context), name="context"),

    path("context/<int:pk>/change/<int:num>/", login_required(views.contract_paragraph_text), name="context_text"),
    path("context/save/", login_required(views.save_context_text), name="save_context_text"),
    
    path("context/new/<int:pk>/", login_required(views.new_context), name="new_context"),
    path("additional/<int:pk>/<int:num>/", login_required(views.additional_view), name="additional"),
    path("add-additional/<int:pk>/", login_required(views.add_additional_view), name="add_additional"),
    path("save-additional/<int:pk>/", login_required(views.save_additional_view), name="save_additional"),

    path("delete/<int:pk>/", login_required(views.delete_contract), name="delete"), 
    path("close/<int:pk>/", login_required(views.close_contract), name="close"),   
    path("cancel/<int:pk>/", login_required(views.cancel_contract), name="cancel"),   

    path("create/withcompany/", login_required(views.create_contract_company), name="create_contract_company"),   
    path("create/with-yatt/", login_required(views.create_contract_yatt), name="create_contract_yatt"),   
    path("create/withperson/", login_required(views.create_contract_person), name="create_contract_person"),   
    
    path("edit/company/<int:pk>/", login_required(views.edit_contract_company), name="edit_contract_company"),
    path("edit/yatt/<int:pk>/", login_required(views.edit_contract_company), name="edit_contract_yatt"),
    path("edit/person/<int:pk>/", login_required(views.edit_contract_person), name="edit_contract_person"),

    path("public/<int:pk>/", login_required(views.make_public_contract), name="public_contract"),
    path("public/<int:pk>/agreement/<int:num>", login_required(views.make_public_agreement), name="public_agreement"),
    
    path("pdf/<uuid:token>/", login_required(views.contract_pdf_view), name="pdf"),
    path("docx/<uuid:token>/", login_required(views.contract_docx_view), name="docx"),
    path("public-pdf/<uuid:token>/", views.public_contract_pdf_view, name="public_contract_pdf"),

    path("pdf/<uuid:token>/agreement/<int:num>/", login_required(views.agreement_pdf_view), name="agreement_pdf"),   
    path("public-pdf/<uuid:token>/agreement/<int:num>/", views.public_agreement_pdf_view, name="public_agreement_pdf_view"),
    
    path("canceled-pdf/<uuid:token>/", login_required(views.contract_canceled_pdf_view), name="canceled_pdf"),
]


#pip install qrcode[pil]
# pip install reportlab
