from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, Order, OrderItem, UserProfile
from .forms import RegisterForm, ProfileForm, CheckoutForm


def home(request):
    featured = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    categories = Category.objects.all()
    return render(request, 'store/home.html', {'products': featured, 'categories': categories})


def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    category_slug = request.GET.get('category')
    search = request.GET.get('q', '')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))

    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'active_category': category_slug,
        'search': search,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {'product': product, 'related': related})


def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0
    for pid, item in cart.items():
        try:
            product = Product.objects.get(id=int(pid))
            subtotal = product.price * item['quantity']
            total += subtotal
            items.append({'product': product, 'quantity': item['quantity'], 'subtotal': subtotal})
        except Product.DoesNotExist:
            pass
    return render(request, 'store/cart.html', {'items': items, 'total': total})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    pid = str(product_id)
    qty = int(request.POST.get('quantity', 1))

    if pid in cart:
        cart[pid]['quantity'] += qty
    else:
        cart[pid] = {'quantity': qty, 'price': str(product.price)}

    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f'{product.name} added to cart!')
    return redirect('cart')


def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    qty = int(request.POST.get('quantity', 1))

    if qty <= 0:
        cart.pop(pid, None)
    else:
        if pid in cart:
            cart[pid]['quantity'] = qty

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    items = []
    total = 0
    for pid, item in cart.items():
        try:
            product = Product.objects.get(id=int(pid))
            subtotal = product.price * item['quantity']
            total += subtotal
            items.append({'product': product, 'quantity': item['quantity'], 'subtotal': subtotal})
        except Product.DoesNotExist:
            pass

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = total
            order.save()

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].price,
                )
                p = item['product']
                p.stock = max(0, p.stock - item['quantity'])
                p.save()

            request.session['cart'] = {}
            messages.success(request, f'Order #{order.id} placed successfully!')
            return redirect('order_confirmation', order_id=order.id)
    else:
        initial = {}
        try:
            profile = request.user.profile
            initial = {'phone': profile.phone, 'shipping_address': profile.address}
        except UserProfile.DoesNotExist:
            pass
        form = CheckoutForm(initial=initial)

    return render(request, 'store/checkout.html', {'items': items, 'total': total, 'form': form})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_confirmation.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account is ready.')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'store/profile.html', {'form': form})