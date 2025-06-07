from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, variation
from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist

# Get or create a cart_id tied to the session
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
            except variation.DoesNotExist:
                pass

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()

    if is_cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        ex_var_list = []
        id_list = []

        for item in cart_items:
            existing_variation = list(item.variations.all())
            ex_var_list.append(existing_variation)
            id_list.append(item.id)

        if product_variations in ex_var_list:
            index = ex_var_list.index(product_variations)
            item_id = id_list[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()
        else:
            new_cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if product_variations:
                new_cart_item.variations.set(product_variations)
            new_cart_item.save()
    else:
        cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        if product_variations:
            cart_item.variations.set(product_variations)
        cart_item.save()

    return redirect('cart')

# Remove a single quantity of a cart item
# Remove a single quantity of a specific variation from cart
def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(cart_id=_cart_id(request))

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

    try:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        for item in cart_items:
            if list(item.variations.all()) == product_variations:
                if item.quantity > 1:
                    item.quantity -= 1
                    item.save()
                else:
                    item.delete()
                break
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')

# Completely remove a specific variation of the cart item
def remove_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(cart_id=_cart_id(request))

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

    try:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        for item in cart_items:
            if list(item.variations.all()) == product_variations:
                item.delete()
                break
    except CartItem.DoesNotExist:
        pass

    return redirect('cart')


# View cart page
def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity

        tax = (2 * total) / 100  # Example tax: 2%
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
