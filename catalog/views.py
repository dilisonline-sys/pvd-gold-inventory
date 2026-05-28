from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from manufacturing.models import FinalProduct
from .models import CatalogSettings


CATALOG_SESSION_KEY = 'catalog_access'


def _is_catalog_auth(request):
    return request.session.get(CATALOG_SESSION_KEY) is True


def catalog_login(request):
    if _is_catalog_auth(request):
        return redirect('catalog:gallery')

    error = None
    if request.method == 'POST':
        password = request.POST.get('password', '')
        settings = CatalogSettings.get()
        if settings.check_password(password):
            request.session[CATALOG_SESSION_KEY] = True
            request.session.set_expiry(60 * 60 * 8)  # 8 hours
            return redirect('catalog:gallery')
        error = 'Incorrect password. Please try again.'

    return render(request, 'catalog/login.html', {'error': error})


def catalog_logout(request):
    request.session.pop(CATALOG_SESSION_KEY, None)
    return redirect('catalog:login')


def catalog_gallery(request):
    if not _is_catalog_auth(request):
        return redirect('catalog:login')

    qs = (
        FinalProduct.objects
        .select_related('production_job', 'production_job__job_order')
        .order_by('-created_at')
    )

    # Filters
    metal = request.GET.get('metal', '').strip()
    finish = request.GET.get('finish', '').strip()
    search = request.GET.get('q', '').strip()

    if metal:
        qs = qs.filter(metal_type__icontains=metal)
    if finish:
        qs = qs.filter(finish=finish)
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(
            production_job__job_number__icontains=search)

    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page'))

    from manufacturing.models import PRODUCT_FINISH_CHOICES
    return render(request, 'catalog/gallery.html', {
        'page_obj': page,
        'products': page.object_list,
        'finish_choices': PRODUCT_FINISH_CHOICES,
        'filter_metal': metal,
        'filter_finish': finish,
        'filter_search': search,
        'total': qs.count(),
    })


def catalog_product(request, pk):
    if not _is_catalog_auth(request):
        return redirect('catalog:login')

    product = get_object_or_404(
        FinalProduct.objects.select_related('production_job', 'created_by'),
        pk=pk,
    )
    return render(request, 'catalog/product_detail.html', {'product': product})
