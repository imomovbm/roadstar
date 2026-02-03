from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import UserProfile
from .models import Mahsulot
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages


# Create your views here.
@login_required
def index(request):
    
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    category = profile.department.category
    product = Mahsulot.objects.filter(category=category)
    # Order and limit
    product = product.order_by('-id')

    return render(request, "products/index.html", {
        "profile": profile,
        "product": product
    })

@login_required
def create_product(request):
    
    profile = get_object_or_404(UserProfile, user=request.user)

    return render(request, "products/detail.html", {
        "profile": profile
    }) 


@login_required
def save_product(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id") or None

        if product_id:
            product = get_object_or_404(Mahsulot, pk=product_id)
            created = False
        else:
            # NEW instance, don’t try to look it up by PK
            product = Mahsulot()
            created = True

        # update fields from the form
        product.item_name    = request.POST.get("name")
        product.category     = request.POST.get("category")
        product.code     = request.POST.get("code")
        product.cypher_code     = request.POST.get("cypher_code")
        product.measurement     = request.POST.get("measurement")
        product.default_cost = request.POST.get("cost")
        product.save()

        if created:
            messages.success(request, "Yangi mahsulot saqlandi.")
        else:
            messages.warning(request, "Mahsulot ma'lumotlari yangilandi.")

        return redirect("products:index")
    # … handle GET or other methods if needed

@login_required
def edit_product(request, pk):
    profile = UserProfile.objects.select_related('user').get(user=request.user)
    product = get_object_or_404(Mahsulot, pk=pk)
    # Order and limit

    return render(request, "products/detail.html", {
        "profile": profile,
        "product": product
    })