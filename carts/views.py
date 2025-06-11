from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

# Get or create a cart ID from the session
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# Add product to cart
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variations = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                var = variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variations.append(var)
            except:
                pass

    if request.user.is_authenticated:
        user = request.user
        cart_item_qs = CartItem.objects.filter(product=product, user=user)
    else:
        cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
        cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

    existing_items = []
    item_ids = []

    for item in cart_item_qs:
        variations = list(item.variations.all())
        existing_items.append(variations)
        item_ids.append(item.id)

    if product_variations in existing_items:
        index = existing_items.index(product_variations)
        item_id = item_ids[index]
        item = CartItem.objects.get(id=item_id)
        item.quantity += 1
        item.save()
    else:
        if request.user.is_authenticated:
            item = CartItem.objects.create(product=product, quantity=1, user=request.user)
        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        if product_variations:
            item.variations.set(product_variations)
        item.save()

    return redirect('cart')

# Remove one quantity from cart item
def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item_qs = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

    product_variations = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                variation_obj = variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variations.append(variation_obj)
            except:
                pass

    for item in cart_item_qs:
        if list(item.variations.all()) == product_variations:
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()
            break

    return redirect('cart')

# Completely remove cart item
def remove_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_authenticated:
        cart_item_qs = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

    product_variations = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                variation_obj = variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variations.append(variation_obj)
            except:
                pass

    for item in cart_item_qs:
        if list(item.variations.all()) == product_variations:
            item.delete()
            break

    return redirect('cart')

# View Cart
def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for item in cart_items:
            total += item.product.price * item.quantity
            quantity += item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        cart_items = []

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

# Checkout (Only for logged-in users)
@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for item in cart_items:
            total += item.product.price * item.quantity
            quantity += item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)

