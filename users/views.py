from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from .models import UserProfile, Client_company, Client_Person, Department
from contracts.models import ContractNew, ContractItem, ActivityLog, Agreement
from products.models import Mahsulot
from .forms import CustomUserForm
from datetime import datetime, timedelta
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
User = get_user_model()

@login_required
def index(request):
    if not request.user.is_authenticated:
        return redirect("users:login")  
    profile = get_object_or_404(UserProfile, user=request.user)

    contracts = ContractNew.objects.count()
    done_deal = ContractNew.objects.filter(done_deal=True).count()
    sold_items = ContractItem.objects.filter(deleted=False).count()
    items = Mahsulot.objects.filter(deleted=False).count()

    # Unique client count from done deals
    done_clients_company_ids = ContractNew.objects.filter(
        done_deal=True, client_company__isnull=False
    ).values_list('client_company_id', flat=True)

    done_clients_person_ids = ContractNew.objects.filter(
        done_deal=True, client_person__isnull=False
    ).values_list('client_person_id', flat=True)

    done_customers = len(set(done_clients_company_ids) | set(done_clients_person_ids))
    
    # calculating 6 months statistics
    six_months_ago = datetime.today().replace(day=1) - timedelta(days=180)
    monthly_stats = (
        ContractNew.objects
        .filter(created_date__gte=six_months_ago)  # adjust field if your date field is named differently
        .annotate(month=TruncMonth('created_date'))
        .values('month')
        .annotate(
            total=Count('id'),
            done=Count('id', filter=Q(done_deal=True)),
            not_done=Count('id', filter=Q(done_deal=False))
        )
        .order_by('month')
    )

    logs = ActivityLog.objects.order_by('-created_at')[:10]  # Latest 10 logs


    return render(request, "users/index.html", {
        "profile": profile,
        "contracts_count": contracts,
        "done_deal":done_deal,
        "items" : items,
        "sold_items" : sold_items,
        "done_customers": done_customers,
        "monthly_stats" : monthly_stats, 
        "logs": logs
    })   

def login_view(request):
    if request.user.is_authenticated:
        return redirect("users:choose_department")

    if request.method == "POST":
        username_post = request.POST["username"]    
        password_post = request.POST["password"] 
        remember = request.POST.get('remember_me')   
        user = authenticate(request, username = username_post, password = password_post)
        if user is not None:
            login(request, user)
            if remember:
                request.session.set_expiry(1209600)  # Expires on browser close
            else:
                request.session.set_expiry(0)  # 2 weeks

            return redirect("users:choose_department")
        else:
            return render(request, "users/pages-login.html", {
                "message": "Login yoki parol xato",
            })
    return render(request, "users/pages-login.html")

def logout_view(request):
    logout(request)
    return redirect("users:login")


@login_required
def choose_department(request):
    departments = Department.objects.all()
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        pk = request.POST.get('department')
        if pk:
            department = get_object_or_404(Department, pk=pk)
            profile.department = department
            profile.save()
            # Redirect to desired page after selection (change 'home' to your url name)
            return redirect('users:index')
        else:
            # Optionally, add a message to indicate selection is required
            error = "Iltimos, tashkilotni tanlang."
            return render(request, "users/choose_department.html", {
                "departments": departments,
                "error": error,
            })

    return render(request, "users/choose_department.html", {
        "departments": departments
    })


@login_required
def user_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, "users/users-profile.html", {
        "profile": profile
    })

def create_user_view(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')  # or any other success page
    else:
        form = CustomUserForm()
    return render(request, 'create_user.html', {'form': form})



@login_required
def save_profile(request):
    if request.method == "POST":
        user_id = request.POST.get("id")
        if str(request.user.id) != user_id:
            messages.error(request, "Siz ushbu profilni tahrirlash huquqiga ega emassiz.")
            return redirect("users:user_profile")
        
        if user_id:
            profile = get_object_or_404(UserProfile, user__id=user_id)

            # ✅ Update user fields
            profile.user.first_name = request.POST.get("first_name", "").strip()
            profile.user.last_name = request.POST.get("last_name", "").strip()
            profile.user.email = request.POST.get("email", "").strip()
            profile.user.save()

            # ✅ Update profile fields
            profile.phone = request.POST.get("phone", "").strip()
            profile.save()

            messages.success(request, "Ma'lumotlar saqlandi.")
        else:
            messages.error(request, "Foydalanuvchi aniqlanmadi.")

    return redirect("users:user_profile")


@login_required
def save_password(request):
    if request.method == "POST":
        user_id = request.POST.get("id")
        
        if str(request.user.id) != user_id:
            messages.error(request, "Siz ushbu profilni tahrirlash huquqiga ega emassiz.")
            return redirect("users:user_profile")

        user = get_object_or_404(User, id=user_id)

        # Form data
        current_password = request.POST.get("password", "").strip()
        new_password = request.POST.get("newpassword", "").strip()
        re_new_password = request.POST.get("renewpassword", "").strip()

        # Check current password
        if not user.check_password(current_password):
            messages.error(request, "Joriy parol noto'g'ri.")
            return redirect("users:user_profile")

        # Check new passwords match
        if new_password != re_new_password:
            messages.error(request, "Yangi parollar mos emas.")
            return redirect("users:user_profile")

        # Set new password
        user.set_password(new_password)
        user.save()

        messages.success(request, "Yangi parol muvaffaqiyatli saqlandi.")
        return redirect("users:user_profile")
    
    
@login_required
def client_person(request):

    profile = get_object_or_404(UserProfile, user=request.user)


    # Base queryset
    person = Client_Person.objects.all().order_by('-id')

    # JSHSHIR (PINFL) filter
    pinfl_number = request.GET.get("pinfl_number")
    if pinfl_number:
        person = person.filter(pinfl__icontains=pinfl_number)
        messages.success(request, f"JSHSHIR: {pinfl_number} bo‘yicha natijalar")

    # Verified status filter
    verified_status = request.GET.get("verified_status")
    if verified_status == "true":
        person = person.filter(verified=True)
        messages.success(request, "Verifikatsiyadan o'tgan mijozlar")
    elif verified_status == "false":
        person = person.filter(verified=False)
        messages.warning(request, "Verifikatsiyadan o'tmagan mijozlar")

    # Limit for performance
    person = person[:200]

    return render(request, "users/person.html", {
        "profile": profile,
        "client_person": person,
        "pinfl_number": pinfl_number,
        "verified_status": verified_status,
    })

@login_required
def client_company(request):

    profile = get_object_or_404(UserProfile, user=request.user)

    # Base queryset
    company = Client_company.objects.filter().order_by('-id')

    # TIN filter
    tin_number = request.GET.get("tin_number")
    if tin_number:
        company = company.filter(tin_number__icontains=tin_number)
        messages.success(request, f"INN: {tin_number} ")


    # Verified status filter
    verified_status = request.GET.get("verified_status")
    if verified_status == "true":
        company = company.filter(verified=True)
        messages.success(request, f'verfikatsiyadan o\'tgan')
    elif verified_status == "false":
        company = company.filter(verified=False)
        messages.warning(request, f'verfikatsiyadan o\'tmagan')

    # If "all" or empty, no filtering

    # Limit to 200 for performance
    company = company[:200]

    return render(request, "users/company.html", {
        "profile": profile,
        "client_company": company,
        "tin_number": tin_number,
        "verified_status": verified_status,
    })

@login_required
def create_client_person(request):

    profile = get_object_or_404(UserProfile, user=request.user)

    return render(request, "users/add_person.html", {
        "profile": profile
    }) 

@login_required
def create_client_yatt(request):
    
    profile = get_object_or_404(UserProfile, user=request.user)

    return render(request, "users/add_yatt.html", {
        "profile": profile
    }) 

@login_required
def save_client_person(request):
    if request.method == "POST":
        person_id = request.POST.get("person_id")
        pinfl = request.POST.get("pinfl")  # primary lookup now
        tin = request.POST.get("tin_number")

        if person_id:
            # Editing existing person
            person = get_object_or_404(Client_Person, pk=person_id)
            created = False
        else:
            # Try to find by PINFL only (primary unique field)
            person = Client_Person.objects.filter(pinfl=pinfl).first()
            if person:
                created = False
            else:
                person = Client_Person(pinfl=pinfl)
                created = True

        # Update or set all fields
        person.tin_number = tin
        person.client_name = request.POST.get("client_name")
        person.address = request.POST.get("address")
        person.passport_number = request.POST.get("passport_number")
        person.phone_number = request.POST.get("phone_number")
        person.email = request.POST.get("email")
        person.head_of_company = request.POST.get("head_of_company")
        person.verified = request.POST.get("verified") == "true"

        person.save()

        if created:
            messages.success(request, "Yangi fuqaro saqlandi.")
        else:
            messages.info(request, "Fuqaro ma'lumotlari yangilandi.")

        return redirect("users:client_person")
    
@login_required
def edit_client_person(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    person = get_object_or_404(Client_Person, pk=pk)
    contracts = ContractNew.objects.filter(client_person=person, partner=profile.department, deleted=False).order_by('-id')

    return render(request, "users/add_person.html", {
        "profile": profile,
        "person": person,
        "contracts": contracts
        })


@login_required
def create_client_company(request):

    profile = get_object_or_404(UserProfile, user=request.user)

    return render(request, "users/add_company.html", {
        "profile": profile
    }) 

@login_required
def create_client_yatt(request):

    profile = get_object_or_404(UserProfile, user=request.user)

    return render(request, "users/add_yatt.html", {
        "profile": profile
    }) 

@login_required
def save_client_company(request):
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        tin = request.POST.get("tin_number")

        if client_id:
            client = get_object_or_404(Client_company, pk=client_id)
            created = False
        else:
            client, created = Client_company.objects.get_or_create(tin_number=tin)

        # ✅ Update fields
        client.tin_number = tin
        client.client_name = request.POST.get("client_name")
        client.address = request.POST.get("address")
        client.account_number = request.POST.get("account_number")
        client.bank_address = request.POST.get("bank_address")
        client.mfo = request.POST.get("mfo")
        client.phone_number = request.POST.get("phone_number")
        client.email = request.POST.get("email")
        client.head_of_company = request.POST.get("head_of_company")
        client.verified = request.POST.get("verified") == "true"

        # ✅ NEW: store JSHSHIR for YATT
        pinfl = request.POST.get("pinfl_number")
        passport_series = request.POST.get("passport_series")
        if pinfl:
            client.pinfl_number_if_yatt = pinfl
            client.passport_series_number_if_yatt = passport_series
        client.save()

        if created:
            messages.success(request, "Yangi mijoz saqlandi.")
        else:
            messages.info(request, "Mijoz ma'lumotlari yangilandi.")

        return redirect("users:client_company")


@login_required
def edit_client_company(request, pk):
    profile = get_object_or_404(UserProfile, user=request.user)
    client = get_object_or_404(Client_company, pk=pk)
    contracts = ContractNew.objects.filter(client_company=client, partner=profile.department, deleted=False).order_by('-id')
    if client.pinfl_number_if_yatt:
        return render(request, "users/add_yatt.html", {
            "profile": profile,
            "client": client,
            "contracts": contracts
            })
    return render(request, "users/add_company.html", {
    "profile": profile,
    "client": client,
    "contracts": contracts
    })

@csrf_exempt
def fetch_company_data(request):
    pinfl = request.GET.get('pinfl')
    passport_series = request.GET.get('passport_series', '')
    tin = request.GET.get('tin')

    if passport_series:
        passport_seria = passport_series[:2]   # first 2 chars
        passport_number = passport_series[2:]  # rest

    if pinfl:
        url = f"https://my3.soliq.uz/api/remote-access-api/entrepreneur/info/{pinfl}?passportSeries={passport_seria}&passportNumber={passport_number}"
    elif tin:
        url = f"https://my3.soliq.uz/api/remote-access-api/company/info/{tin}?type=full"
    else:
        return JsonResponse({'error': 'INN yoki JSHSHIR kiriting'}, status=400)
    
    headers = {
        "X-API-KEY": "6a70e885-3387-49ca-8dd2-54a3242604d7",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    try:
        data = response.json()  # ✅ try parsing JSON
    except ValueError:
        # If it's not JSON, return raw text for debugging
        return JsonResponse({
            'error': "API noto‘g‘ri formatda javob qaytardi",
            'status_code': response.status_code,
            'raw_response': response.text[:500]  # limit to first 500 chars
        }, status=500)

    if response.status_code == 200:
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({
            'error': "Ma'lumotni olishda xatolik",
            'status_code': response.status_code,
            'details': data
        }, status=response.status_code)


@csrf_exempt
def check_company(request):
    tin = request.GET.get("tin")
    yatt = request.GET.get("yatt")
    if not [tin, yatt]:
        return JsonResponse({'exists': False}, status=400)
    company = None
    if tin:
        company = Client_company.objects.filter(tin_number=tin).first()
    elif yatt:
        company = Client_company.objects.filter(pinfl_number_if_yatt=yatt).first()

    if company:
        return JsonResponse({
            'exists': True, 
            'type': 'Yuridik shaxs', 
            'pinfl_number': company.pinfl_number_if_yatt, 
            'tin_number': company.tin_number, 
            'name': company.client_name, 
            'address': company.address, 
            'account_number': company.account_number, 
            'mfo': company.mfo,
            'bank_address': company.bank_address, 
            'phone_number': company.phone_number, 
            'head_of_company': company.head_of_company, 
            'email': company.email,
            'verified': company.verified,
            'id': company.pk  # This should be returning the correct ID
        })
    else:
        return JsonResponse({'exists': False}, status=404)


@csrf_exempt
def check_person(request):
    pinfl = request.GET.get("pinfl")
    if not pinfl:
        return JsonResponse({'error': 'PINFL parameter is required'}, status=400)
    
    try:
        person = Client_Person.objects.get(pinfl=pinfl)
        return JsonResponse({
            'exists': True, 
            'type': 'Jismoniy shaxs', 
            'name': person.client_name, 
            'address': person.address, 
            'pinfl_number': person.pinfl, 
            'tin_number': person.tin_number, 
            'passport_number': person.passport_number, 
            'phone_number': person.phone_number, 
            'email': person.email, 
            'head_of_company': person.head_of_company, 
            'verified': person.verified,
            'id': person.pk
        })
    except Client_Person.DoesNotExist:
        return JsonResponse({'exists': False}, status=404)



@login_required
def departments(request):

    profile = UserProfile.objects.select_related('user').get(user=request.user)
    department = Department.objects.all()
    # Order and limit
    department = department.order_by('-id')

    return render(request, "users/department.html", {
        "profile": profile,
        "department": department
    })

@login_required
def create_department(request):

    profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, "users/add_department.html", {
        "profile": profile
    }) 

@login_required
def save_department(request):
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        tin = request.POST.get("tin_number")

        if department_id:
            department = get_object_or_404(Department, pk=department_id)
            created = False
        else:
            department, created = Department.objects.get_or_create(tin_number=tin)

        # ✅ Update fields
        department.tin_number = tin
        department.department_name = request.POST.get("department")
        department.address = request.POST.get("address")
        department.account_number = request.POST.get("account_number")
        department.bank_address = request.POST.get("bank_address")
        department.mfo = request.POST.get("mfo")
        department.phone_number = request.POST.get("phone_number")
        department.head_of_company = request.POST.get("head_of_company")
        department.category = request.POST.get("category")
        department.save()

        if created:
            messages.success(request, "Yangi tashkilot saqlandi.")
        else:
            messages.info(request, "Tashkilot ma'lumotlari yangilandi.")
        return redirect("users:departments")

@login_required
def edit_department(request, pk):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    department = get_object_or_404(Department, pk=pk)
    # Order and limit

    return render(request, "users/add_department.html", {
        "profile": profile,
        "department": department
    })