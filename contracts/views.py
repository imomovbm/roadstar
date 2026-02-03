from django.shortcuts import render, redirect, get_object_or_404
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from users.models import UserProfile, Client_company, Client_Person
from django.utils.dateparse import parse_date
from .models import ContractNew, ContractItem, ContractContext, ActivityLog, Agreement, AgreementContext
from products.models import Mahsulot 
from django.contrib import messages
from datetime import timedelta
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from contracts.utils import get_default_paragraph_text, generate_contract_pdf, generate_contract_canceled_pdf, get_qr_image_base64, get_qr_agreement_base64, clean_html_text,send_custom_email, send_custom_email_with_attachment, send_sms_ibnux, generate_agreement_pdf, generate_contract_docx
import re
from django.contrib.contenttypes.models import ContentType
from datetime import date


@login_required
def index(request): 

    profile = UserProfile.objects.select_related('user').get(user=request.user)
    contracts = ContractNew.objects.filter(deleted=False, partner = profile.department.pk)

    date_range = request.GET.get("date_range")
    if date_range:
        try:
            parts = [s.strip() for s in date_range.split("to")]
            if len(parts) == 2:
                start_date = parse_date(parts[0])
                end_date = parse_date(parts[1])
            elif len(parts) == 1:
                start_date = end_date = parse_date(parts[0])
            else:
                start_date = end_date = None

            if start_date and end_date:
                # include the end_date fully by adding one day and using __lt
                contracts = contracts.filter(created_date__gte=start_date, created_date__lt=end_date + timedelta(days=1))
            else:
                messages.warning(request, "Sanani tanlashda xatolik. Iltimos, to‘g‘ri formatda kiriting.")
        except Exception:
            messages.warning(request, "Sanani tanlashda xatolik. Iltimos, to‘g‘ri formatda kiriting.")    
        # --- Contract Status filter ---
    contract_status = request.GET.get("contract_status")
    if contract_status == "closed":
        contracts = contracts.filter(done_deal=True)
    elif contract_status == "open":
        contracts = contracts.filter(done_deal=False)
    # "all" or None shows everything
    
    # Order and limit
    contracts = contracts.order_by('-id')[:200]

    return render(request, "contracts/index.html", {
        "profile": profile,
        "contracts": contracts
    })


@login_required
def edit_contract_company(request, pk):
    # 1) Fetch the contract + lookup lists
    contract = get_object_or_404(ContractNew, pk=pk)
    profile  = UserProfile.objects.select_related('user').get(user=request.user)
    items    = Mahsulot.objects.filter(deleted=False).order_by('item_name')
    if contract.done_deal == True:
        return redirect('contracts:detail', pk=contract.pk)
    
    if request.method == "POST":
        # — resolve client_id just like in create —
        client_id = request.POST.get('client_id')
        contract.client_company = Client_company.objects.get(pk=client_id)
        
        # — update other simple fields —
        contract.manager = request.POST.get('manager', "").strip()
        contract.partner = profile.department

        # — 1) Flush out old items — 
        contract.contract_items.all().delete()

        # — 2) Recreate items & recompute total —
        total = Decimal(0)
        product_ids = request.POST.getlist('product[]')
        costs       = request.POST.getlist('cost[]')
        amounts     = request.POST.getlist('amount[]')

        for pid, cost_str, qty_str in zip(product_ids, costs, amounts):
            try:
                cost = Decimal(cost_str)
            except:
                cost = Decimal(0)
            try:
                qty = int(qty_str)
            except:
                qty = 0

            total += cost * qty

            ContractItem.objects.create(
                contract=contract,
                item_id=pid,
                cost=cost,
                amount=qty,
            )

        # — 3) Save the new sum & contract changes —
        contract.summ = total
        contract.save()

        if contract:
            ActivityLog.objects.create(
                author=request.user,
                event='edit',
                content_type=ContentType.objects.get_for_model(ContractNew),
                object_id=contract.pk,
            )   

        return redirect('contracts:detail', pk=contract.pk)

    # GET → render the same form, passing in `contract` so the template
    # can pre-fill all values
    return render(request, "contracts/create_contract_company.html", {
        "profile": profile,
        "contract": contract,
        "client": contract.client_company,
        "items": items,
    })


@login_required
def edit_contract_person(request, pk):
    # 1) Fetch the contract + lookup lists
    contract = get_object_or_404(ContractNew, pk=pk)
    profile  = UserProfile.objects.select_related('user').get(user=request.user)
    items    = Mahsulot.objects.filter(deleted=False).order_by('item_name')
    if contract.done_deal == True:
        return redirect('contracts:detail', pk=contract.pk)
    
    if request.method == "POST":
        # — resolve client_id just like in create —
        person_id = request.POST.get('person_id')
        contract.client_person = Client_Person.objects.get(pk=person_id)
        
        # — update other simple fields —
        contract.manager = request.POST.get('manager', "").strip()
        contract.partner = profile.department

        # — 1) Flush out old items — 
        contract.contract_items.all().delete()

        # — 2) Recreate items & recompute total —
        total = Decimal(0)
        product_ids = request.POST.getlist('product[]')
        costs       = request.POST.getlist('cost[]')
        amounts     = request.POST.getlist('amount[]')

        for pid, cost_str, qty_str in zip(product_ids, costs, amounts):
            try:
                cost = Decimal(cost_str)
            except:
                cost = Decimal(0)
            try:
                qty = int(qty_str)
            except:
                qty = 0

            total += cost * qty

            ContractItem.objects.create(
                contract=contract,
                item_id=pid,
                cost=cost,
                amount=qty,
            )

        # — 3) Save the new sum & contract changes —
        contract.summ = total
        contract.save()

        if contract:
            ActivityLog.objects.create(
                author=request.user,
                event='edit',
                content_type=ContentType.objects.get_for_model(ContractNew),
                object_id=contract.pk,
            )   

        return redirect('contracts:detail', pk=contract.pk)

    # GET → render the same form, passing in `contract` so the template
    # can pre-fill all values
    return render(request, "contracts/create_contract_person.html", {
        "profile": profile,
        "contract": contract,
        "person": contract.client_person,
        "items": items,
    })


@login_required
def create_contract_company(request):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    items = Mahsulot.objects.filter(deleted=False,category=profile.department.category).order_by('item_name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        tin_number = request.POST.get('tin_number')
        verified = request.POST.get('verified', 'false').lower() == 'true'

        client_company = None
        # 1. Try to get by ID
        if client_id:
            try:
                client_company = Client_company.objects.get(pk=client_id)
            except Client_company.DoesNotExist:
                pass
        # 3. Try to get by TIN
        if not client_company and tin_number:
            try:
                client_company = Client_company.objects.get(tin_number=tin_number)
            except Client_company.DoesNotExist:
                pass
        # 4. If not found, create new
        if not client_company:
            client_company = Client_company.objects.create(
                client_name=request.POST.get('client_name'),
                address=request.POST.get('address'),
                tin_number=tin_number,
                account_number=request.POST.get('account_number'),
                bank_address=request.POST.get('bank_address'),
                mfo=request.POST.get('mfo'),
                phone_number=request.POST.get('phone_number'),
                email=request.POST.get('email'),
                head_of_company=request.POST.get('head_of_company'),
                verified=verified,
            )
        else:
            # If found, update all fields
            client_company.client_name = request.POST.get('client_name')
            client_company.address = request.POST.get('address')
            client_company.tin_number = tin_number
            client_company.account_number = request.POST.get('account_number')
            client_company.bank_address = request.POST.get('bank_address')
            client_company.mfo = request.POST.get('mfo')
            client_company.phone_number = request.POST.get('phone_number')
            client_company.email = request.POST.get('email')
            client_company.head_of_company = request.POST.get('head_of_company')
            client_company.verified = verified
            client_company.save()


        manager_post = request.POST.get('manager', '').strip()
        is_public_post = request.POST.get("is_public") == "true"

        # 4) Build the code: "<pk>/<director-initials>"
        last_contract = ContractNew.objects.filter(partner=profile.department).order_by("-pk").first()
        last_code_num = int(last_contract.code) if (last_contract and last_contract.code) else 0

        # 3) Create the bare ContractNew (code & summ will be set after)
        contract = ContractNew.objects.create(
            author=request.user,
            partner = profile.department,
            manager=manager_post,
            client_company=client_company,
            is_public = is_public_post,
            code=str(last_code_num + 1)
        )


        # 5) Process line items & compute total sum
        total = Decimal(0)
        product_ids = request.POST.getlist('product[]')
        costs       = request.POST.getlist('cost[]')
        amounts     = request.POST.getlist('amount[]')

        for pid, cost_str, qty_str in zip(product_ids, costs, amounts):
            # parse values safely
            try:
                cost = Decimal(cost_str)
            except:
                cost = Decimal(0)
            try:
                qty = int(qty_str)
            except:
                qty = 0

            line_total = cost * qty
            total += line_total

            # create each ContractItem
            ContractItem.objects.create(
                contract=contract,
                item_id=pid,
                cost=cost,
                amount=qty,
            )

        # 6) Save the aggregate sum and code
        contract.summ = total
        contract.save()

        
        if contract:
            ActivityLog.objects.create(
                author=request.user,
                event='create',
                content_type=ContentType.objects.get_for_model(ContractNew),
                object_id=contract.pk,
            )

        today = date.today()
        if client_company.email:
            pdf_file = generate_contract_pdf(contract.pk)  # must return BytesIO

            subject = f"{contract.code} shartnoma"
            body = (
                f"Hurmatli tadbirkor {client_company.client_name}, siz va "
                f"{contract.partner.department_name} bilan {today} da tuzilgan "
                f"summasi {contract.summ:,} so'm {contract.code} raqamli shartnoma imzolash uchun yuborildi."
                f"Quyida biz sizga shartnomani ilova qilib yuboryapmiz."
            ) 
             
            send_custom_email_with_attachment(
                subject=subject,
                body=body,
                recipient_list=[client_company.email],
                sender_email=f"{profile.department.email}",  
                sender_password=f"{profile.department.app_password}",
                pdf_file=pdf_file,
                filename=f"{client_company.client_name}_{contract.code}.pdf"
            )

        try:
            link = ''
            if contract.public_token:
                link = f"https://roadstar.uz/contracts/public-pdf/{contract.public_token}/"

            if client_company.phone_number:
                

                # First message: greeting and contract info
                message = (
                    f"Hurmatli tadbirkor {client_company.client_name}, siz va "
                    f"{contract.partner.department_name} bilan {today} da tuzilgan "
                    f"summasi {contract.summ:,} so'm {contract.code}-raqamli shartnoma imzolash uchun Didox orqali yuborildi. "
                    f"Shartnomani yuklash: {link}"
                )

                send_sms_ibnux(client_company.phone_number, message)
        except:
            messages.warning(request, "SMS yuborishda xatolik!")

        return redirect('contracts:detail', pk=contract.pk)
    
    return render(request, "contracts/create_contract_company.html", {
    "profile": profile,
    "items": items,
    })

@login_required
def create_contract_yatt(request):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    items = Mahsulot.objects.filter(deleted=False,category=profile.department.category).order_by('item_name')

    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        pinfl_number = request.POST.get('pinfl_number')
        passport_series = request.POST.get('passport_series')
        tin_number = request.POST.get('tin_number')
        verified = request.POST.get('verified', 'false').lower() == 'true'

        client_company = None
        # 1. Try to get by ID
        if client_id:
            try:
                client_company = Client_company.objects.get(pk=client_id)
            except Client_company.DoesNotExist:
                pass
        # 2. Try to get by PINFL
        if not client_company and pinfl_number:
            try:
                client_company = Client_company.objects.get(pinfl_number_if_yatt=pinfl_number)
            except Client_company.DoesNotExist:
                pass
        # 4. If not found, create new
        if not client_company:
            client_company = Client_company.objects.create(
                client_name=request.POST.get('client_name'),
                address=request.POST.get('address'),
                tin_number=tin_number,
                pinfl_number_if_yatt=pinfl_number,
                passport_series_number_if_yatt=passport_series,
                account_number=request.POST.get('account_number'),
                bank_address=request.POST.get('bank_address'),
                mfo=request.POST.get('mfo'),
                phone_number=request.POST.get('phone_number'),
                email=request.POST.get('email'),
                head_of_company=request.POST.get('head_of_company'),
                verified=verified,
            )
        else:
            # If found, update all fields
            client_company.client_name = request.POST.get('client_name')
            client_company.address = request.POST.get('address')
            client_company.tin_number = tin_number
            client_company.pinfl_number_if_yatt = pinfl_number
            client_company.passport_series_number_if_yatt = passport_series
            client_company.account_number = request.POST.get('account_number')
            client_company.bank_address = request.POST.get('bank_address')
            client_company.mfo = request.POST.get('mfo')
            client_company.phone_number = request.POST.get('phone_number')
            client_company.email = request.POST.get('email')
            client_company.head_of_company = request.POST.get('head_of_company')
            client_company.verified = verified
            client_company.save()


        manager_post = request.POST.get('manager', '').strip()
        is_public_post = request.POST.get("is_public") == "true"

        # 4) Build the code: "<pk>/<director-initials>"
        last_contract = ContractNew.objects.filter(partner=profile.department).order_by("-pk").first()
        last_code_num = int(last_contract.code) if (last_contract and last_contract.code) else 0

        # 3) Create the bare ContractNew (code & summ will be set after)
        contract = ContractNew.objects.create(
            author=request.user,
            partner = profile.department,
            manager=manager_post,
            client_company=client_company,
            is_public = is_public_post,
            code=str(last_code_num + 1),
        )


        # 5) Process line items & compute total sum
        total = Decimal(0)
        product_ids = request.POST.getlist('product[]')
        costs       = request.POST.getlist('cost[]')
        amounts     = request.POST.getlist('amount[]')

        for pid, cost_str, qty_str in zip(product_ids, costs, amounts):
            # parse values safely
            try:
                cost = Decimal(cost_str)
            except:
                cost = Decimal(0)
            try:
                qty = int(qty_str)
            except:
                qty = 0

            line_total = cost * qty
            total += line_total

            # create each ContractItem
            ContractItem.objects.create(
                contract=contract,
                item_id=pid,
                cost=cost,
                amount=qty,
            )

        # 6) Save the aggregate sum and code
        contract.summ = total
        contract.save()

        
        if contract:
            ActivityLog.objects.create(
                author=request.user,
                event='create',
                content_type=ContentType.objects.get_for_model(ContractNew),
                object_id=contract.pk,
            )

        today = date.today()
        if client_company.email:
            pdf_file = generate_contract_pdf(contract.pk)  # must return BytesIO

            subject = f"{contract.code} shartnoma"
            body = (
                f"Hurmatli tadbirkor {client_company.client_name}, siz va "
                f"{contract.partner.department_name} bilan {today} da tuzilgan "
                f"summasi {contract.summ:,} so'm {contract.code} raqamli shartnoma imzolash uchun yuborildi."
                f"Quyida biz sizga shartnomani ilova qilib yuboryapmiz."
            ) 
             
            send_custom_email_with_attachment(
                subject=subject,
                body=body,
                recipient_list=[client_company.email],
                sender_email=f"{profile.department.email}",  
                sender_password=f"{profile.department.app_password}",
                pdf_file=pdf_file,
                filename=f"{client_company.client_name}_{contract.code}.pdf"
            )

        try:
            link = ''
            if contract.public_token:
                link = f"https://roadstar.uz/contracts/public-pdf/{contract.public_token}/"

            if client_company.phone_number:
                

                # First message: greeting and contract info
                message = (
                    f"Hurmatli tadbirkor {client_company.client_name}, siz va "
                    f"{contract.partner.department_name} bilan {today} da tuzilgan "
                    f"summasi {contract.summ:,} so'm {contract.code}-raqamli shartnoma imzolash uchun Didox orqali yuborildi. "
                    f"Shartnomani yuklash: {link}"
                )

                send_sms_ibnux(client_company.phone_number, message)
        except:
            messages.warning(request, "SMS yuborishda xatolik!")

        return redirect('contracts:detail', pk=contract.pk)
    
    return render(request, "contracts/create_contract_yatt.html", {
    "profile": profile,
    "items": items,
    })

@login_required
def create_contract_person(request):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    items = Mahsulot.objects.filter(deleted=False,category=profile.department.category).order_by('item_name')

    if request.method == 'POST':
        client_id = request.POST.get('person_id')
        pinfl_number = request.POST.get('pinfl_number')
        verified = request.POST.get('verified', 'false').lower() == 'true'
        tin_number=request.POST.get('tin_number')
        client_person = None

        if client_id:
            try:
                client_person = Client_Person.objects.get(pk=client_id)
            except Client_Person.DoesNotExist:
                pass
        
        if not client_person and pinfl_number:
            try:
                client_person = Client_Person.objects.get(pinfl=pinfl_number)
            except Client_Person.DoesNotExist:
                pass
            
        if not client_person and tin_number:
            try:
                client_person = Client_Person.objects.get(tin_number=tin_number)
            except Client_Person.DoesNotExist:
                pass   
        if not client_person:        
            # 3. Otherwise, create new
            client_person = Client_Person.objects.create(
                client_name=request.POST.get('client_name'),
                address=request.POST.get('address'),
                tin_number=tin_number,
                passport_number=request.POST.get('passport_number'),
                phone_number=request.POST.get('phone_number'),
                head_of_company=request.POST.get('head_of_company'),
                email=request.POST.get('email'),
                verified=verified,
                pinfl=pinfl_number
            )

        manager_post = request.POST.get('manager', '').strip()
        is_public_post = request.POST.get("is_public") == "true"

        # 4) Build the code: "<pk>/<director-initials>"
        last_contract = ContractNew.objects.filter(partner=profile.department).order_by("-pk").first()
        last_code_num = int(last_contract.code) if (last_contract and last_contract.code) else 0

        # 3) Create the bare ContractNew (code & summ will be set after)
        contract = ContractNew.objects.create(
            author=request.user,
            partner = profile.department,
            manager=manager_post,
            client_person=client_person,
            is_public = is_public_post,
            code=str(last_code_num + 1),
        )


        # 5) Process line items & compute total sum
        total = Decimal(0)
        product_ids = request.POST.getlist('product[]')
        costs       = request.POST.getlist('cost[]')
        amounts     = request.POST.getlist('amount[]')

        for pid, cost_str, qty_str in zip(product_ids, costs, amounts):
            # parse values safely
            try:
                cost = Decimal(cost_str)
            except:
                cost = Decimal(0)
            try:
                qty = int(qty_str)
            except:
                qty = 0

            line_total = cost * qty
            total += line_total

            # create each ContractItem
            ContractItem.objects.create(
                contract=contract,
                item_id=pid,
                cost=cost,
                amount=qty,
            )

        # 6) Save the aggregate sum and code
        contract.summ = total
        contract.save()

        
        if contract:
            ActivityLog.objects.create(
                author=request.user,
                event='create',
                content_type=ContentType.objects.get_for_model(ContractNew),
                object_id=contract.pk,
            )

        today = date.today()
        if client_person.email:
            pdf_file = generate_contract_pdf(contract.pk)  # must return BytesIO

            subject = f"{contract.code} shartnoma"
            body = (
                f"Hurmatli tadbirkor {client_person.client_name}, siz va "
                f"{contract.partner.department_name} bilan {today} da tuzilgan "
                f"summasi {contract.summ:,} so'm {contract.code} raqamli shartnoma imzolash uchun yuborildi."
                f"Quyida biz sizga shartnomani ilova qilib yuboryapmiz."
            ) 
            
            send_custom_email_with_attachment(
                subject=subject,
                body=body,
                recipient_list=[client_person.email],
                sender_email=f"{profile.department.email}",  
                sender_password=f"{profile.department.app_password}",
                pdf_file=pdf_file,
                filename=f"{client_person.client_name}_{contract.code}.pdf"
            )

        try:
            link = ''
            if contract.public_token:
                link = f"https://roadstar.uz/contracts/public-pdf/{contract.public_token}/"
            if client_person.phone_number:
                
                message = (
                    f"Hurmatli tadbirkor {client_person.client_name}, " 
                    f"siz va {contract.partner.department_name} bilan "
                    f"{today} da tuzilgan summasi {contract.summ:,} so'm "
                    f"{contract.code}-raqamli shartnoma imzolash uchun Didox orqali yuborildi. "
                    f"Shartnomani yuklash: {link}"
                )
                send_sms_ibnux(client_person.phone_number, message)
        except:
            messages.warning(request, "SMS yuborishda xatolik!")

        return redirect('contracts:detail', pk=contract.pk)
    
    return render(request, "contracts/create_contract_person.html", {
    "profile": profile,
    "items": items,
    })

@login_required
def contract_detail(request, pk):
    
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    # print(ContractNew.objects.filter(pk=pk))
        # Only fetch contracts that are not deleted
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)
    # Custom context paragraphs
    custom_contexts = ContractContext.objects.filter(
        contract=contract,
        deleted=False
    )

    context_dict = {}
    for o in custom_contexts:
        context_dict[(o.paragraph_number, o.key, o.value)] = o.paragraph_text    

    all_paragraph_numbers = sorted(contract.paragraph_numbers)
    paragraphs = []

    for para_num in all_paragraph_numbers:
        defaults = get_default_paragraph_text(para_num)
        # Get header
        header = context_dict.get((para_num, 'header', 1), defaults['header'][1])
        # Get all subparagraphs
        text_dict = {}
        for subkey, subval in defaults['text'].items():
            text_dict[subkey] = context_dict.get((para_num, 'text', subkey), subval)
        paragraphs.append({
            "number": para_num,
            "header": header,
            "text": text_dict,
        })

    
    sales = ContractItem.objects.filter(
        deleted=False,
        contract_id=contract.pk
    ).exclude(item='1').select_related('item')

    qr = None
    if contract.is_public and contract.public_token:
        qr = get_qr_image_base64(contract.pk)

    last = max(all_paragraph_numbers)+1
    return render(request, "contracts/detail.html", {
        "profile": profile,
        "contract": contract,
        "sales": sales,
        "paragraphs": paragraphs,
        "qr": qr,
        "last":last
    })


@login_required
def contract_context(request, pk):

    profile = UserProfile.objects.select_related('user').get(user=request.user)
    # print(ContractNew.objects.filter(pk=pk))
        # Only fetch contracts that are not deleted
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)
    # Custom context paragraphs
    custom_contexts = ContractContext.objects.filter(
        contract=contract,
        deleted=False
    )
    context_dict = {}
    for o in custom_contexts:
        context_dict[(o.paragraph_number, o.key, o.value)] = o.paragraph_text    

    all_paragraph_numbers = sorted(contract.paragraph_numbers)
    paragraphs = []

    for para_num in all_paragraph_numbers:
        defaults = get_default_paragraph_text(para_num)
        # Get header
        header = context_dict.get((para_num, 'header', 1), defaults['header'][1])
        # Get all subparagraphs
        text_dict = {}
        for subkey, subval in defaults['text'].items():
            text_dict[subkey] = context_dict.get((para_num, 'text', subkey), subval)
        paragraphs.append({
            "number": para_num,
            "header": header,
            "text": text_dict,
        })


    return render(request, "contracts/context.html", {
        "profile": profile,
        "contract": contract,
        "paragraphs": paragraphs,
        "all_paragraph_numbers": all_paragraph_numbers,

    })

@login_required
def contract_paragraph_text(request, pk, num):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)

    # Gather all overrides for this contract & paragraph
    custom_contexts = ContractContext.objects.filter(contract=contract, paragraph_number=num, deleted=False)
    context_dict = {}
    for o in custom_contexts:
        context_dict[(o.key, o.value)] = o.paragraph_text

    # Get default structure
    defaults = get_default_paragraph_text(num)
    # Prepare unified data
    paragraph = {
        "number": num,
        "header": context_dict.get(('header', 1), defaults['header'][1]),
        "text": {},
    }
    for subkey, subval in defaults['text'].items():
        paragraph["text"][subkey] = context_dict.get(('text', subkey), subval)

    return render(request, "contracts/context_paragraph_edit.html", {
        "profile": profile,
        "contract": contract,
        "paragraph_num": num,
        "paragraph": paragraph,  # now you have all fields for editing
    })

@require_POST
def save_context_text(request):
    pk = request.POST.get('id')
    num = int(request.POST.get('num'))  # Make sure this is an int

    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)

    # Get defaults
    defaults = get_default_paragraph_text(num)
    default_header = defaults['header'][1]
    default_texts = defaults['text']

    # --- Handle header ---
    header = request.POST.get('header', '').strip()
    if header != default_header:
        # Save/update custom header
        obj, created = ContractContext.objects.update_or_create(
            contract=contract,
            paragraph_number=num,
            key='header',
            value=1,
            defaults={'paragraph_text': header, 'deleted': False}
        )
    else:
        # If a custom header exists, but now matches default, delete it
        ContractContext.objects.filter(
            contract=contract,
            paragraph_number=num,
            key='header',
            value=1,
            deleted=False
        ).delete()

    # --- Handle subparagraphs ---
    for subkey, default_value in default_texts.items():
        field_name = f'text_{subkey}'
        posted_value = request.POST.get(field_name, '').strip()
        posted_value = clean_html_text(posted_value)
        if posted_value != clean_html_text(default_value):
            # Save/update custom subparagraph
            obj, created = ContractContext.objects.update_or_create(
                contract=contract,
                paragraph_number=num,
                key='text',
                value=subkey,
                defaults={'paragraph_text': posted_value, 'deleted': False}
            )
        else:
            # If a custom exists, but now matches default, delete it
            ContractContext.objects.filter(
                contract=contract,
                paragraph_number=num,
                key='text',
                value=subkey,
                deleted=False
            ).delete()

    messages.success(request, "Paragraf saqlandi!")
    return redirect('contracts:context', pk=contract.pk)


@login_required
def new_context(request, pk):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)

    # Find the next available paragraph number
    num = max(contract.paragraph_numbers) + 1 if contract.paragraph_numbers else 1

    if request.method == 'POST':
        header = request.POST.get('header', '')
        text = request.POST.get('text')
        
        header = clean_html_text(header)
        text = clean_html_text(text)        
        
        # Save header row
        header_obj = ContractContext.objects.create(
            contract=contract,
            paragraph_number=num,
            key='header',
            value=1,
            paragraph_text=header,
            deleted=False
        )
        
        # Save first subparagraph row (value=1 by default for a new paragraph)
        text_obj = ContractContext.objects.create(
            contract=contract,
            paragraph_number=num,
            key='text',
            value=1,
            paragraph_text=text,
            deleted=False
        )
        # Update the contract's paragraph_numbers array
        if num not in contract.paragraph_numbers:
            contract.paragraph_numbers.append(num)
            contract.save()

        if header_obj and text_obj:
            messages.success(request, "Yangi paragraf saqlandi!")
        else:
            messages.warning(request, "Yangi paragraf saqlanmadi!")
        return redirect('contracts:context', pk=contract.pk)
   
    return render(request, "contracts/create_new_context.html", {
        "profile": profile,
        "contract": contract,
        "paragraph_num": num,
    })

@require_POST
def delete_contract(request, pk):
    contract = get_object_or_404(ContractNew, pk=pk)
    if contract.done_deal == True:
        messages.warning(request, f"Shartnoma {contract.code} muvaffaqiyatli yopilgan. Uni o'chirolmaysiz")
        return redirect('contracts:detail', pk=contract.pk)
    contract.deleted = True
    contract.save()
    if contract:
        ActivityLog.objects.create(
            author=request.user,
            event='delete',
            content_type=ContentType.objects.get_for_model(ContractNew),
            object_id=contract.pk,
        )
    messages.warning(request, f"Shartnoma {contract.code} muvaffaqiyatli o'chirildi.")
    return redirect('contracts:index')
# You can also use messages.warning, messages.info, or messages.error.

    

@require_POST
def close_contract(request, pk):
    contract = get_object_or_404(ContractNew, pk=pk)
    if contract.deleted == True:
        messages.danger(request, f"Shartnoma {contract.code} o'chirilgan!")
        return redirect('contracts:detail', pk=contract.pk)
    contract.done_deal = True
    contract.save()
    if contract:
        ActivityLog.objects.create(
            author=request.user,
            event='edit',
            content_type=ContentType.objects.get_for_model(ContractNew),
            object_id=contract.pk,
        )
    messages.success(request, f"Shartnoma {contract.code} muvaffaqiyatli imzolandi.")
    if contract.get_client().email:
        send_custom_email(
            subject=f'{contract.code} shartnoma',
            message=f' Hurmatli {contract.get_client().client_name} sizning {contract.partner.department_name} bilan {contract.code} raqamli, {contract.summ} so\'mli shartnomangiz muvaffaqiyatli tasdiqlandi.',
            recipient_list=[f'{contract.get_client().email}'],
            sender_email=f"{contract.partner.email}",
            sender_password=f"{contract.partner.app_password}"
        )
    return redirect('contracts:detail', pk=contract.pk)
# You can also use messages.warning, messages.info, or messages.error.

@require_POST
def cancel_contract(request, pk):
    contract = get_object_or_404(ContractNew, pk=pk)
    if contract.canceled == True:
        messages.danger(request, f"Shartnoma {contract.code} o'chirilgan!")
        return redirect('contracts:detail', pk=contract.pk)
    contract.canceled = True
    contract.save()

    messages.warning(request, f"Shartnoma {contract.code} bekor qilindi.")
    if contract.get_client().email:
        send_custom_email(
            subject=f'{contract.code} shartnoma',
            message=f' Hurmatli {contract.get_client().client_name} sizning {contract.partner.department_name} bilan {contract.code} raqamli, {contract.summ} so\'mli shartnomangiz bekor qilindi.',
            recipient_list=[f'{contract.get_client().email}'],
            sender_email=f"{contract.partner.email}",
            sender_password=f"{contract.partner.app_password}"
        )
    return redirect('contracts:detail', pk=contract.pk)
# You can also use messages.warning, messages.info, or messages.error.


@login_required
def make_public_contract(request, pk):
    contract = get_object_or_404(ContractNew, pk=pk)
    contract.is_public = True
    contract.save()
    if contract:
        ActivityLog.objects.create(
            author=request.user,
            event='edit',
            content_type=ContentType.objects.get_for_model(ContractNew),
            object_id=contract.pk,
        )
    messages.info(request, f"Shartnoma {contract.code} uchun QR kod yaratildi.")
    return redirect('contracts:detail', pk=contract.pk)
# You can also use messages.warning, messages.info, or messages.error.

@login_required
def contract_pdf_view(request, token):
    contract = get_object_or_404(ContractNew, public_token=token, is_public=True, deleted=False)
    return generate_contract_pdf(contract.pk)

@login_required
def contract_docx_view(request, token):
    contract = get_object_or_404(ContractNew, public_token=token, is_public=True, deleted=False)
    return generate_contract_docx(contract.pk)

@login_required
def contract_canceled_pdf_view(request, token):
    contract = get_object_or_404(ContractNew, public_token=token, is_public=True, deleted=False)
    return generate_contract_canceled_pdf(contract.pk)

@csrf_exempt
def public_contract_pdf_view(request, token):
    contract = get_object_or_404(ContractNew, public_token=token, is_public=True, deleted=False)
    if not contract.is_public:
        return HttpResponse("Ushbu shartnoma ommaviy ko‘rinishda emas.", status=403)
    return generate_contract_pdf(contract.pk)

@login_required
def add_additional_view(request, pk):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)
    subparagraphs_to_edit = []

    if request.method == "POST":
        selected_items = request.POST.getlist('items[]')
        selected_subparagraphs = []
        for val in selected_items:
            para_num, subkey = map(int, val.split('-'))
            selected_subparagraphs.append((para_num, subkey))

        # Get custom and default text for each selected subparagraph
        for para_num, subkey in selected_subparagraphs:
            # First, try to find custom override
            ctx = ContractContext.objects.filter(
                contract=contract,
                paragraph_number=para_num,
                key='text',
                value=subkey,
                deleted=False
            ).first()
            if ctx:
                text = ctx.paragraph_text
            else:
                # Fallback to default
                defaults = get_default_paragraph_text(para_num)
                text = defaults['text'].get(subkey, "")

            subparagraphs_to_edit.append({
                "paragraph_number": para_num,
                "subkey": subkey,
                "text": text,
            })

    return render(request, "contracts/create_new_additional.html", {
        "profile": profile,
        "contract": contract,
        "subparagraphs_to_edit": subparagraphs_to_edit,
    })


@login_required
def save_additional_view(request, pk):
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)

    if request.method == 'POST':
        code = 1
        agreement = Agreement.objects.filter(contract=contract).order_by('-id').first()
        if agreement:
            try:
                code = int(agreement.code or 0) + 1
            except (TypeError, ValueError):
                code = 1

        agreement = Agreement.objects.create(contract=contract, code=code)
        saved = False
        for key in request.POST:
            if key.startswith('text_'):
                _, para_num, subkey = key.split('_')
                paragraph_number = f"{para_num}.{subkey}"
                paragraph_text = request.POST.get(key, '').strip()

                if paragraph_text:
                    paragraph_text = clean_html_text(paragraph_text)
                    AgreementContext.objects.create(
                        agreement_num= agreement,
                        paragraph_number = paragraph_number,
                        paragraph_text = paragraph_text,
                        deleted = False
                    )
                    saved = True                    

        if saved:
            messages.success(request, "Qo'shimcha shartnoma bandlari saqlandi!")
        else:
            messages.warning(request, "Hech qanday band saqlanmadi!")

        return redirect('contracts:additional', pk=contract.pk, num=agreement.pk)
    return redirect('contracts:detail', pk=contract.pk)


@login_required
def additional_view(request, pk, num):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    contract = get_object_or_404(ContractNew, pk=pk, deleted=False)
    additional = Agreement.objects.filter(contract=contract, pk=num, deleted=False).first()
    context_of_additional = AgreementContext.objects.filter(agreement_num=additional, deleted=False)

    qr = None
    if contract.public_token and additional.is_public:
        qr = get_qr_agreement_base64(contract.pk, additional.pk)

    return render(request, "contracts/additional_agreement.html", {
        "profile": profile,
        "contract": contract,
        "additional": additional,
        "context": context_of_additional,
        "qr": qr
    })

@login_required
def agreement_pdf_view(request, token, num):
    contract = get_object_or_404(ContractNew, public_token=token, is_public=True, deleted=False)
    additional = Agreement.objects.filter(contract=contract, pk=num, deleted=False).first()
    return generate_agreement_pdf(contract.pk, additional.pk)

@csrf_exempt
def public_agreement_pdf_view(request, token, num):
    contract = get_object_or_404(ContractNew, public_token=token, is_public=True, deleted=False)
    additional = Agreement.objects.filter(contract=contract, pk=num, deleted=False).first()
    if not additional.is_public:
        return HttpResponse("Ushbu shartnoma ommaviy ko‘rinishda emas.", status=403)
    return generate_agreement_pdf(contract.pk, additional.pk)


@login_required
def make_public_agreement(request, pk, num):
    contract = get_object_or_404(ContractNew, pk=pk)
    if not contract.is_public:
        contract.is_public = True
        contract.save()

    additional = Agreement.objects.filter(contract=contract, pk=num, deleted=False).first()
    additional.is_public = True
    additional.save()

    messages.success(request, f"Shartnoma {contract.code}ning {additional.pk}-qo'shimcha kelishuvi uchun QR kod yaratildi.")
    return redirect('contracts:additional', pk=contract.pk, num=additional.pk)
# You can also use messages.warning, messages.info, or messages.error.