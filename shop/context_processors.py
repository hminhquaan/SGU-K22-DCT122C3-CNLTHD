from .models import Cart


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        count = cart.total_items
    return {"cart_count": count}
