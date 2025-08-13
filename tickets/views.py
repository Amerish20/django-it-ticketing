from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Ticket, Item, Department,LeaveType,RequestForm,Application
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.hashers import check_password
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import datetime
from django.views.decorators.http import require_POST
from django.contrib.auth import logout

def login_view(request):
    if request.method == 'POST':
        batch_number = request.POST.get('batch_number')
        password = request.POST.get('password')
        try:
            user = User.objects.get(batch_number=batch_number, status=1)  # status is IntegerField
            if password == user.password:
                request.session['frontend_user_id'] = user.id
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid credentials or inactive user.')
    return render(request, 'login.html')

def create_ticket(request):
    user_id = request.session.get('frontend_user_id')
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

    return render(request, 'base.html', {'user': user, 'items': items,'tickets': user_tickets})

def logout_view(request):
    request.session.flush()
    return redirect('login')

def dashboard(request):
    user_id = request.session.get('frontend_user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    leave_types = LeaveType.objects.filter(status=1)
    request_forms = RequestForm.objects.filter(status=1)
    return render(request, 'dashboard.html', {
        'user': user,
        'leave_types': leave_types,
        'request_forms': request_forms
    })

def submit_application(request):
    if request.method == 'POST':
        user = User.objects.get(id=request.session.get('frontend_user_id'))
        request_form_name = request.POST.get('request_form')

        if request_form_name.lower() == 'leave':
            leave_type = request.POST.get('leave_type')
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            remarks = request.POST.get('remarks')
            total_days = (datetime.datetime.strptime(to_date, "%Y-%m-%d") - datetime.datetime.strptime(from_date, "%Y-%m-%d")).days + 1

            Application.objects.create(
                user=user,
                leave_type_id=leave_type,
                request_form=RequestForm.objects.get(name__iexact='Leave'),
                from_date=from_date,
                to_date=to_date,
                total_days=total_days,
                remarks=remarks,
                status="Pending",
                entry_date=datetime.datetime.now()
            )

        elif request_form_name.lower() == 'clearance':
            # Save clearance details here
            pass

        elif request_form_name.lower() == 'salary advance':
            # Save salary advance info
            pass

        messages.success(request, f"{request_form_name.title()} request submitted.")
        return redirect('my_applications')
def my_applications(request):
    user_id = request.session.get('frontend_user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.get(id=user_id)
    applications = Application.objects.filter(user=user, delete_status=False).order_by('-entry_date')[:10]
    leave_types = LeaveType.objects.filter(status=1)
    request_forms = RequestForm.objects.filter(status=1)  # or whatever logic you use

    return render(request, 'my_applications.html', {
        'applications': applications,
        'leave_types': leave_types,
        'request_forms': request_forms,  # for the apply form/modal
        'user': user,  # if you need to prefill user data
    })

def edit_application(request, application_id):
    app = get_object_or_404(Application, id=application_id, delete_status=False)
    leave_types = LeaveType.objects.filter(status=1)

    if app.status != 'Pending':
        return JsonResponse({'error': 'Only pending applications can be edited.'}, status=403)

    if request.method == 'POST':
        from_date = request.POST.get('from_date')  # YYYY-MM-DD
        to_date = request.POST.get('to_date')      # YYYY-MM-DD
        remarks = request.POST.get('remarks')
        leave_type_id = request.POST.get('leave_type')

        if not from_date or not to_date:
            return JsonResponse({'error': 'From Date and To Date are required.'})

        try:
            from_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
            to_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Please use YYYY-MM-DD.'})

        if from_dt > to_dt:
            return JsonResponse({'error': 'From Date cannot be after To Date.'})
        

        if leave_type_id:
            try:
                lt = LeaveType.objects.get(id=leave_type_id, status=1)
                app.leave_type = lt
            except LeaveType.DoesNotExist:
                return JsonResponse({'error': 'Invalid leave type selected.'})
        else:
            return JsonResponse({'error': 'Leave Type is required.'})

        app.from_date = from_dt
        app.to_date = to_dt
        app.remarks = remarks
        app.total_days = (to_dt - from_dt).days + 1
        app.save()

        return JsonResponse({'success': True})

    # Format for HTML date input
    app.from_date_display = app.from_date.strftime("%Y-%m-%d") if app.from_date else ""
    app.to_date_display = app.to_date.strftime("%Y-%m-%d") if app.to_date else ""

    html = render_to_string('partials/edit_application_modal.html', {
        'application': app,
        'leave_types': leave_types
    },request=request)
    return HttpResponse(html)

@require_POST
def delete_application(request, application_id):
    app = get_object_or_404(Application, id=application_id)

    if app.status != 'Pending':
        return JsonResponse({'error': 'Only pending applications can be marked deleted.'}, status=403)

    app.delete_status = True
    app.save()

    return JsonResponse({'success': True})
    
def custom_logout(request):
    logout(request)
    return render(request, "admin/logged_out.html")