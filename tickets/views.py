from django.shortcuts import render, redirect
from .models import User, Ticket, Item
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.hashers import check_password

def login_view(request):
    if request.method == 'POST':
        batch_number = request.POST.get('batch_number')
        password = request.POST.get('password')
        try:
            user = User.objects.get(batch_number=batch_number, status=1)  # status is IntegerField
            print(check_password(password, user.password))
            if password == user.password:
                request.session['user_id'] = user.id
                return redirect('create_ticket')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid credentials or inactive user.')
    return render(request, 'login.html')

def create_ticket(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    items = Item.objects.filter(status=True)
    user_tickets = Ticket.objects.filter(user=user).order_by('-request_date')[:10]

    if request.method == 'POST':
        item_id = request.POST.get('item')
        description = request.POST.get('description')
        item = Item.objects.get(id=item_id)
        Ticket.objects.create(user=user, item=item, description=description)
        messages.success(request, 'Ticket submitted successfully!')
        return redirect('create_ticket')

    return render(request, 'create_ticket.html', {'user': user, 'items': items,'tickets': user_tickets})

def logout_view(request):
    request.session.flush()
    return redirect('login')
