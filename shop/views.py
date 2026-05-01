from decimal import Decimal
from datetime import timedelta
from urllib.parse import urlencode
import hashlib
import hmac
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import re
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, RegisterForm
from .models import Cart, CartItem, Category, Order, OrderItem, Product, UserProfile


def _cart_summary(cart):
    items = cart.items.select_related("product", "product__category")
    subtotal = cart.subtotal
    shipping_fee = Decimal("30000.00") if subtotal > 0 else Decimal("0.00")
    total = subtotal + shipping_fee
    return items, subtotal, shipping_fee, total


def _vnpay_configured():
    return all(
        getattr(settings, attribute_name, "")
        for attribute_name in ("VNPAY_URL", "VNPAY_TMN_CODE", "VNPAY_HASH_SECRET")
    )


def _vnpay_sign(payload):
    sign_data = "&".join(f"{key}={payload[key]}" for key in sorted(payload))
    return hmac.new(settings.VNPAY_HASH_SECRET.encode("utf-8"), sign_data.encode("utf-8"), hashlib.sha512).hexdigest()


def _user_has_staff_role(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.is_staff_role)


def _build_vnpay_payment_url(request, order):
    if not _vnpay_configured():
        return None

    now = timezone.localtime(timezone.now())
    vnpay_params = {
        "vnp_Amount": str(int(order.total_amount * 100)),
        "vnp_Command": "pay",
        "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
        "vnp_CurrCode": "VND",
        "vnp_ExpireDate": (now + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S"),
        "vnp_IpAddr": request.META.get("REMOTE_ADDR", "127.0.0.1"),
        "vnp_IpnUrl": request.build_absolute_uri(reverse("vnpay_ipn")),
        "vnp_Locale": "vn",
        "vnp_OrderInfo": f"Thanh toan don hang {order.display_tracking_code}",
        "vnp_OrderType": "other",
        "vnp_ReturnUrl": request.build_absolute_uri(reverse("vnpay_return")),
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_TxnRef": order.display_tracking_code,
        "vnp_Version": "2.1.0",
    }
    query_params = urlencode(vnpay_params)
    secure_hash = _vnpay_sign(vnpay_params)
    return f"{settings.VNPAY_URL}?{query_params}&vnp_SecureHash={secure_hash}"


def _verify_vnpay_return(request):
    received_hash = request.GET.get("vnp_SecureHash", "")
    payload = {
        key: value
        for key, value in request.GET.items()
        if key not in {"vnp_SecureHash", "vnp_SecureHashType"}
    }
    if not received_hash:
        return False
    return hmac.compare_digest(_vnpay_sign(payload).lower(), received_hash.lower())


def _finalize_payment_success(order):
    if order.payment_status == Order.PAYMENT_PAID:
        return False
    if order.payment_status in {Order.PAYMENT_FAILED, Order.PAYMENT_CANCELLED}:
        return False

    order.payment_status = Order.PAYMENT_PAID
    order.order_status = Order.STATUS_CONFIRMED
    order.confirmed_at = order.confirmed_at or timezone.now()
    order.save(update_fields=["payment_status", "order_status", "confirmed_at", "updated_at"])
    return True


def _finalize_payment_failure(order, *, cancelled=False):
    if order.payment_status == Order.PAYMENT_PAID:
        return False
    if order.payment_status in {Order.PAYMENT_FAILED, Order.PAYMENT_CANCELLED}:
        return False

    order.restore_inventory_and_cart()
    order.payment_status = Order.PAYMENT_CANCELLED if cancelled else Order.PAYMENT_FAILED
    order.order_status = Order.STATUS_CANCELLED
    order.cancelled_at = order.cancelled_at or timezone.now()
    order.save(update_fields=["payment_status", "order_status", "cancelled_at", "updated_at"])
    return True


def _vnpay_result_is_cancelled(response_code, transaction_status):
    return response_code == "24" or transaction_status == "02"


def _sync_vnpay_payment(order, response_code, transaction_status):
    if response_code == "00" and transaction_status == "00":
        return "success", _finalize_payment_success(order)
    if _vnpay_result_is_cancelled(response_code, transaction_status):
        return "cancelled", _finalize_payment_failure(order, cancelled=True)
    return "failed", _finalize_payment_failure(order, cancelled=False)


def _google_maps_configured():
    return bool(getattr(settings, "GOOGLE_MAPS_API_KEY", ""))


def _fetch_json(url):
    request_headers = {
        "User-Agent": "ZENITH-FITNESS/1.0 (address autocomplete)",
        "Accept": "application/json",
    }
    with urlopen(Request(url, headers=request_headers), timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))


def _first_component(components, type_name):
    for component in components or []:
        if type_name in component.get("types", []):
            return component.get("long_name") or component.get("short_name") or ""
    return ""


def _google_place_details_payload(place):
    address_components = place.get("address_components", []) or []
    street_number = _first_component(address_components, "street_number")
    route = _first_component(address_components, "route")
    ward = _first_component(address_components, "sublocality_level_1") or _first_component(address_components, "sublocality") or _first_component(address_components, "neighborhood")
    district = _first_component(address_components, "administrative_area_level_2")
    province = _first_component(address_components, "administrative_area_level_1")
    postcode = _first_component(address_components, "postal_code")
    street_address = " ".join(part for part in [street_number, route] if part).strip() or place.get("name", "").strip()
    formatted_address = place.get("formatted_address", "").strip()
    detail = _normalize_address_line(street_address, ward, district, province, postcode) or formatted_address
    return {
        "label": street_address or place.get("name", "").strip() or formatted_address,
        "detail": detail,
        "street_address": street_address,
        "ward": ward,
        "district": district,
        "province": province,
        "postcode": postcode,
        "lat": str(place.get("geometry", {}).get("location", {}).get("lat", "")),
        "lon": str(place.get("geometry", {}).get("location", {}).get("lng", "")),
        "place_type": _normalize_address_line(place.get("business_status", ""), ",".join(place.get("types", [])[:2])),
    }


def _google_autocomplete_results(query):
    params = {
        "input": query,
        "language": "vi",
        "components": "country:vn",
        "types": "address",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?{urlencode(params)}"
    try:
        payload = _fetch_json(url)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return []

    if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
        return []

    results = []
    for item in payload.get("predictions", []):
        formatting = item.get("structured_formatting", {}) or {}
        results.append(
            {
                "label": formatting.get("main_text") or item.get("description", ""),
                "detail": formatting.get("secondary_text") or item.get("description", ""),
                "place_id": item.get("place_id", ""),
                "provider": "google",
                "types": item.get("types", []),
                "description": item.get("description", ""),
            }
        )
    return results


def _google_place_detail(place_id):
    params = {
        "place_id": place_id,
        "fields": "formatted_address,address_component,geometry,name,types,business_status",
        "language": "vi",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    url = f"https://maps.googleapis.com/maps/api/place/details/json?{urlencode(params)}"
    try:
        payload = _fetch_json(url)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    if payload.get("status") != "OK":
        return None

    result = payload.get("result", {}) or {}
    detailed = _google_place_details_payload(result)
    detailed["provider"] = "google"
    detailed["place_id"] = place_id
    return detailed


def _nominatim_reverse_location(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 18,
        "accept-language": "vi",
    }
    url = f"https://nominatim.openstreetmap.org/reverse?{urlencode(params)}"
    try:
        payload = _fetch_json(url)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    address = payload.get("address", {}) or {}
    house_number = _pick_address_value(address, ["house_number"])
    road = _pick_address_value(address, ["road", "pedestrian", "footway", "path", "street"])
    ward = _pick_address_value(address, ["suburb", "quarter", "neighbourhood", "city_district", "residential", "borough"])
    district = _pick_address_value(address, ["county", "district", "city_district", "town", "city", "municipality", "village", "hamlet"])
    province = _pick_address_value(address, ["state", "region"])
    postcode = _pick_address_value(address, ["postcode"])
    street_address = " ".join(part for part in [house_number, road] if part).strip() or payload.get("name", "").strip()
    detail = _normalize_address_line(street_address, ward, district, province, postcode) or payload.get("display_name", "")

    return {
        "label": street_address or payload.get("name", "").strip() or detail,
        "detail": detail,
        "street_address": street_address,
        "ward": ward,
        "district": district,
        "province": province,
        "postcode": postcode,
        "lat": str(lat),
        "lon": str(lon),
        "place_type": _normalize_address_line(payload.get("class", ""), payload.get("type", "")),
        "provider": "nominatim",
    }


def _pick_address_value(address, keys):
    for key in keys:
        value = address.get(key, "")
        if value:
            return value
    return ""


def _normalize_address_line(*parts):
    return ", ".join(dict.fromkeys(part.strip() for part in parts if part and part.strip()))


def address_suggestions(request):
    query = request.GET.get("q", "").strip()
    place_id = request.GET.get("place_id", "").strip()
    lat = request.GET.get("lat", "").strip()
    lon = request.GET.get("lon", "").strip()

    if place_id and _google_maps_configured():
        detailed = _google_place_detail(place_id)
        if detailed:
            return JsonResponse({"results": [detailed]})
        return JsonResponse({"results": []})

    if lat and lon:
        if _google_maps_configured():
            params = {
                "latlng": f"{lat},{lon}",
                "language": "vi",
                "key": settings.GOOGLE_MAPS_API_KEY,
            }
            url = f"https://maps.googleapis.com/maps/api/geocode/json?{urlencode(params)}"
            try:
                payload = _fetch_json(url)
            except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
                payload = None
            if payload and payload.get("status") == "OK":
                results = []
                for result in payload.get("results", []):
                    address_components = result.get("address_components", []) or []
                    street_number = _first_component(address_components, "street_number")
                    route = _first_component(address_components, "route")
                    ward = _first_component(address_components, "sublocality_level_1") or _first_component(address_components, "sublocality") or _first_component(address_components, "neighborhood")
                    district = _first_component(address_components, "administrative_area_level_2")
                    province = _first_component(address_components, "administrative_area_level_1")
                    postcode = _first_component(address_components, "postal_code")
                    street_address = " ".join(part for part in [street_number, route] if part).strip() or result.get("name", "").strip()
                    detail = _normalize_address_line(street_address, ward, district, province, postcode) or result.get("formatted_address", "")
                    results.append(
                        {
                            "label": street_address or result.get("name", "").strip() or detail,
                            "detail": detail,
                            "street_address": street_address,
                            "ward": ward,
                            "district": district,
                            "province": province,
                            "postcode": postcode,
                            "lat": str(lat),
                            "lon": str(lon),
                            "place_type": _normalize_address_line(result.get("business_status", ""), ",".join(result.get("types", [])[:2])),
                            "provider": "google",
                        }
                    )
                if results:
                    return JsonResponse({"results": results})

        detailed = _nominatim_reverse_location(lat, lon)
        if detailed:
            return JsonResponse({"results": [detailed]})
        return JsonResponse({"results": []})

    if len(query) < 3:
        return JsonResponse({"results": []})

    if _google_maps_configured():
        google_results = _google_autocomplete_results(query)
        if google_results:
            return JsonResponse({"results": google_results})

    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "namedetails": 1,
        "extratags": 1,
        "dedupe": 1,
        "limit": 8,
        "countrycodes": "vn",
        "accept-language": "vi",
    }
    url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
    try:
        payload = _fetch_json(url)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return JsonResponse({"results": []})

    results = []
    for item in payload:
        address = item.get("address", {}) or {}
        house_number = _pick_address_value(address, ["house_number"])
        road = _pick_address_value(address, ["road", "pedestrian", "footway", "path", "street"])
        suburb = _pick_address_value(address, ["suburb", "quarter", "neighbourhood", "city_district", "residential", "borough"])
        district = _pick_address_value(address, ["county", "district", "city_district", "town", "city", "municipality", "village", "hamlet"])
        province = _pick_address_value(address, ["state", "region"])
        postcode = _pick_address_value(address, ["postcode"])

        street_address = " ".join(part for part in [house_number, road] if part).strip() or item.get("name", "").strip()
        if not street_address:
            street_address = item.get("display_name", "").split(",")[0].strip()

        detail_parts = [
            street_address,
            suburb,
            district,
            province,
            postcode,
        ]
        detail = _normalize_address_line(*detail_parts) or item.get("display_name", "")
        label = street_address or item.get("name", "").strip() or detail
        if label and detail and label.lower() != detail.lower() and detail.lower() not in label.lower():
            label = f"{label}"

        results.append(
            {
                "label": label,
                "detail": detail,
                "street_address": street_address,
                "ward": suburb,
                "district": district,
                "province": province,
                "postcode": postcode,
                "lat": item.get("lat", ""),
                "lon": item.get("lon", ""),
                "place_type": _normalize_address_line(item.get("class", ""), item.get("type", "")),
                "provider": "nominatim",
            }
        )

    return JsonResponse({"results": results})


def product_list(request):
    category_slug = request.GET.get("category", "")
    search_query = request.GET.get("q", "").strip()
    sort_option = request.GET.get("sort", "newest")
    categories = Category.objects.filter(is_active=True)
    products = Product.objects.select_related("category").filter(is_active=True)

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=selected_category)

    if search_query:
        products = products.filter(name__icontains=search_query)

    sort_map = {
        "newest": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
    }
    products = products.order_by(sort_map.get(sort_option, "-created_at"))

    paginator = Paginator(products, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "index.html",
        {
            "products": page_obj,
            "page_obj": page_obj,
            "categories": categories,
            "selected_category": selected_category,
            "search_query": search_query,
            "sort_option": sort_option,
        },
    )


def home_view(request):
    featured_products = Product.objects.select_related("category").filter(is_active=True)[:4]
    spotlight_products = Product.objects.select_related("category").filter(is_active=True)[:6]
    categories = Category.objects.filter(is_active=True)[:4]
    return render(
        request,
        "home.html",
        {
            "featured_products": featured_products,
            "spotlight_products": spotlight_products,
            "categories": categories,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category"), slug=slug, is_active=True)
    return render(request, "product_detail.html", {"product": product})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.select_related("category").filter(category=category, is_active=True)

    sort_option = request.GET.get("sort", "newest")
    sort_map = {
        "newest": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
    }
    products = products.order_by(sort_map.get(sort_option, "-created_at"))

    paginator = Paginator(products, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "category_detail.html",
        {
            "category": category,
            "products": page_obj,
            "page_obj": page_obj,
            "sort_option": sort_option,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("product_list")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Đăng ký thành công. Chào mừng bạn đến với ZENITH FITNESS.")
        return redirect("product_list")

    return render(request, "registration/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Bạn đã đăng xuất.")
    return redirect("product_list")


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get("quantity", 1))
    quantity = max(1, quantity)

    if quantity > product.stock:
        messages.error(request, f"Chỉ còn {product.stock} sản phẩm trong kho.")
        return redirect("product_detail", slug=product.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})

    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            messages.error(request, f"Số lượng trong giỏ không thể vượt quá tồn kho hiện có ({product.stock}).")
            return redirect("view_cart")
        cart_item.quantity = new_quantity
        cart_item.save(update_fields=["quantity", "updated_at"])

    messages.success(request, f"Đã thêm {product.name} vào giỏ hàng.")
    return redirect("view_cart")


@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items, subtotal, shipping_fee, total = _cart_summary(cart)

    return render(
        request,
        "cart.html",
        {
            "cart": cart,
            "items": items,
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "total": total,
        },
    )


@login_required
def order_list(request):
    if _user_has_staff_role(request.user):
        orders = Order.objects.all().prefetch_related("items", "items__product")
    else:
        orders = Order.objects.filter(user=request.user).prefetch_related("items", "items__product")
    return render(request, "orders.html", {"orders": orders})


@login_required
def order_tracking(request):
    if _user_has_staff_role(request.user):
        orders = Order.objects.all().prefetch_related("items", "items__product")
    else:
        orders = Order.objects.filter(user=request.user).prefetch_related("items", "items__product")
    tracking_code = request.GET.get("tracking_code", "").strip().upper()
    focused_order = None

    if tracking_code:
        focused_order = orders.filter(tracking_code=tracking_code).first()
        if focused_order is None:
            match = re.fullmatch(r"ZF(\d{6})", tracking_code)
            if match:
                focused_order = orders.filter(id=int(match.group(1))).first()

    if focused_order is None:
        focused_order = orders.first()

    return render(
        request,
        "tracking.html",
        {
            "orders": orders,
            "focused_order": focused_order,
            "tracking_code": tracking_code,
        },
    )


@login_required
def order_detail(request, order_id):
    order_queryset = Order.objects.prefetch_related("items", "items__product")
    if not _user_has_staff_role(request.user):
        order_queryset = order_queryset.filter(user=request.user)
    order = get_object_or_404(order_queryset, id=order_id)
    return render(request, "order_detail.html", {"order": order})


@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
    return redirect("view_cart")


@login_required
@transaction.atomic
@require_POST
def update_cart_item(request, item_id, action):
    cart = get_object_or_404(Cart.objects.select_for_update(), user=request.user)
    cart_item = get_object_or_404(CartItem.objects.select_for_update(), id=item_id, cart=cart)

    if action == "increase":
        if cart_item.quantity >= cart_item.product.stock:
            messages.error(request, f"Chỉ còn {cart_item.product.stock} sản phẩm trong kho.")
            return redirect("view_cart")
        cart_item.quantity += 1
        cart_item.save(update_fields=["quantity", "updated_at"])
        messages.success(request, "Đã tăng số lượng sản phẩm.")
    elif action == "decrease":
        if cart_item.quantity <= 1:
            cart_item.delete()
            messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
            return redirect("view_cart")
        cart_item.quantity -= 1
        cart_item.save(update_fields=["quantity", "updated_at"])
        messages.success(request, "Đã giảm số lượng sản phẩm.")

    return redirect("view_cart")


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    items, subtotal, shipping_fee, total = _cart_summary(cart)

    if not items.exists():
        messages.warning(request, "Giỏ hàng đang trống.")
        return redirect("view_cart")

    if request.method == "GET":
        form = CheckoutForm(
            initial={
                "full_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
            }
        )
        return render(
            request,
            "checkout.html",
            {
                "cart": cart,
                "items": items,
                "subtotal": subtotal,
                "shipping_fee": shipping_fee,
                "total": total,
                "checkout_form": form,
            },
        )

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "checkout.html",
            {
                "cart": cart,
                "items": items,
                "subtotal": subtotal,
                "shipping_fee": shipping_fee,
                "total": total,
                "checkout_form": form,
            },
        )

    full_name = form.cleaned_data["full_name"]
    phone = form.cleaned_data["phone"]
    email = form.cleaned_data["email"]
    province = form.cleaned_data["province"]
    district = form.cleaned_data["district"].strip()
    ward = form.cleaned_data["ward"].strip()
    street_address = form.cleaned_data["street_address"].strip()
    shipping_address = form.cleaned_data["shipping_address"]
    note = form.cleaned_data["note"]
    payment_method = form.cleaned_data["payment_method"]
    delivery_place_name = form.cleaned_data.get("delivery_place_name", "")
    delivery_place_id = form.cleaned_data.get("delivery_place_id", "")
    delivery_map_provider = form.cleaned_data.get("delivery_map_provider", "")
    delivery_latitude = form.cleaned_data.get("delivery_latitude")
    delivery_longitude = form.cleaned_data.get("delivery_longitude")

    subtotal = sum(item.product.price * item.quantity for item in items)
    shipping_fee = Decimal("30000.00") if subtotal > 0 else Decimal("0.00")
    total_amount = subtotal + shipping_fee

    with transaction.atomic():
        cart = get_object_or_404(Cart.objects.select_for_update(), user=request.user)
        items = list(cart.items.select_related("product").select_for_update())

        for item in items:
            if item.product.stock < item.quantity:
                messages.error(request, f"Sản phẩm {item.product.name} không đủ tồn kho.")
                return redirect("view_cart")

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            email=email,
            province=province,
            district=district,
            ward=ward,
            street_address=street_address,
            delivery_place_name=delivery_place_name,
            delivery_place_id=delivery_place_id,
            delivery_map_provider=delivery_map_provider,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            shipping_address=shipping_address,
            note=note,
            subtotal=subtotal,
            total_amount=total_amount,
            payment_method=payment_method,
            payment_status=Order.PAYMENT_PENDING,
            order_status=Order.STATUS_PENDING,
        )

        order_items = []
        for item in items:
            order_items.append(
                OrderItem(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    unit_price=item.product.price,
                    quantity=item.quantity,
                    line_total=item.product.price * item.quantity,
                )
            )
            Product.objects.filter(id=item.product.id).update(stock=F("stock") - item.quantity)

        OrderItem.objects.bulk_create(order_items)
        cart.items.all().delete()

    tracking_code = order.display_tracking_code
    payment_label = order.get_payment_method_display()
    if order.is_online_payment:
        messages.info(
            request,
            f"Đơn hàng đã được tạo với mã theo dõi {tracking_code}. Hãy hoàn tất thanh toán để đơn được xác nhận.",
        )
    else:
        messages.success(request, f"Đặt hàng thành công. Mã theo dõi của bạn là {tracking_code}. Phương thức thanh toán: {payment_label}.")
    if order.is_online_payment:
        return redirect("order_payment", order_id=order.id)
    return redirect(f"{reverse('order_tracking')}?tracking_code={tracking_code}")


@login_required
def order_payment(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product"),
        id=order_id,
        user=request.user,
    )

    if not order.is_online_payment:
        return redirect("order_detail", order_id=order.id)

    payment_details = order.payment_details

    if request.method == "POST":
        order.payment_status = Order.PAYMENT_PAID
        order.order_status = Order.STATUS_CONFIRMED
        order.confirmed_at = order.confirmed_at or timezone.now()
        order.save(update_fields=["payment_status", "order_status", "confirmed_at", "updated_at"])
        messages.success(request, "Thanh toán đã được ghi nhận.")
        return redirect(f"{reverse('order_tracking')}?tracking_code={order.display_tracking_code}")

    return render(
        request,
        "payment.html",
        {
            "order": order,
            "payment_details": payment_details,
            "tracking_url": f"{reverse('order_tracking')}?tracking_code={order.display_tracking_code}",
            "payment_url": _build_vnpay_payment_url(request, order) if order.payment_method == Order.METHOD_VNPAY else "",
        },
    )


@login_required
@require_POST
def order_payment_cancel(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "items__product"),
        id=order_id,
        user=request.user,
    )

    if not order.is_online_payment:
        return redirect("order_detail", order_id=order.id)

    with transaction.atomic():
        order = Order.objects.select_for_update().prefetch_related("items", "items__product").get(id=order.id, user=request.user)
        if _finalize_payment_failure(order, cancelled=True):
            messages.warning(request, "Bạn đã hủy thanh toán. Đơn hàng không được xác nhận.")
        else:
            messages.info(request, "Đơn hàng đã ở trạng thái cuối cùng trước đó.")

    return redirect(f"{reverse('order_tracking')}?tracking_code={order.display_tracking_code}")


def vnpay_return(request):
    if not _verify_vnpay_return(request):
        messages.error(request, "Dữ liệu thanh toán trả về không hợp lệ.")
        return redirect("product_list")

    tracking_code = request.GET.get("vnp_TxnRef", "").strip().upper()
    order = get_object_or_404(Order, tracking_code=tracking_code)

    response_code = request.GET.get("vnp_ResponseCode", "")
    transaction_status = request.GET.get("vnp_TransactionStatus", "")
    outcome, changed = _sync_vnpay_payment(order, response_code, transaction_status)
    if outcome == "success":
        if changed:
            messages.success(request, "Thanh toán VNPay đã được xác nhận. Đơn hàng đã thành công.")
        else:
            messages.info(request, "Đơn hàng đã được thanh toán trước đó.")
    elif outcome == "cancelled":
        messages.warning(request, "Bạn đã hủy thanh toán VNPay. Đơn hàng không thành công.")
    else:
        messages.warning(request, "Thanh toán chưa hoàn tất hoặc bị từ chối bởi cổng VNPay. Đơn hàng không thành công.")

    return redirect(f"{reverse('order_tracking')}?tracking_code={order.display_tracking_code}")


def vnpay_ipn(request):
    if not _verify_vnpay_return(request):
        return JsonResponse({"RspCode": "97", "Message": "Invalid signature"})

    tracking_code = request.GET.get("vnp_TxnRef", "").strip().upper()
    order = Order.objects.filter(tracking_code=tracking_code).first()
    if order is None:
        return JsonResponse({"RspCode": "01", "Message": "Order not found"})

    response_code = request.GET.get("vnp_ResponseCode", "")
    transaction_status = request.GET.get("vnp_TransactionStatus", "")
    outcome, changed = _sync_vnpay_payment(order, response_code, transaction_status)
    if outcome == "success" and changed:
        return JsonResponse({"RspCode": "00", "Message": "Confirm Success"})
    if outcome == "success":
        return JsonResponse({"RspCode": "02", "Message": "Order already confirmed"})
    if outcome == "cancelled":
        return JsonResponse({"RspCode": "00", "Message": "Cancel recorded"})
    return JsonResponse({"RspCode": "00", "Message": "Payment failed recorded"})
