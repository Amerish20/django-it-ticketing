from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Ticket, Item, Department,LeaveType,RequestForm,Application, Month, Year,DepartmentHead
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.hashers import check_password,make_password
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from datetime import datetime
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from datetime import date
import pdfkit
from django.templatetags.static import static
import calendar
from .utils import send_application_email,find_department_head_email
from django.urls import reverse
from urllib.parse import urlencode

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

    return render(request, 'create_ticket.html', {'user': user, 'items': items,'tickets': user_tickets})

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
    months = Month.objects.all()
    years = Year.objects.filter(status=1).order_by('year')
    # fetch last approved leave (not sick leave) for rejoining
    last_leave = (
        Application.objects.filter(
            user=user,
            status="Approved"
        )
        .exclude(leave_type__name__iexact="Sick Leave")
        .order_by("-to_date")
        .first()
    )
    return render(request, 'dashboard.html', {
        'user': user,
        'leave_types': leave_types,
        'request_forms': request_forms,
        'last_leave': last_leave,
        'months': months,
        'years': years,
        
    })

def submit_application(request):
    if request.method == 'POST':
        user = User.objects.get(id=request.session.get('frontend_user_id'))
        request_form_id = request.POST.get('request_form')
        request_form = RequestForm.objects.get(id=request_form_id)
        email_sent = False
        new_app = None
        # Find Department Head email via department + name match
        auth_details = find_department_head_email(user)
        # Leave
        if request_form_id == '1': 
            leave_type = request.POST.get('leave_type')
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            remarks = request.POST.get('remarks')
            to_date_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            from_date_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            format_to_date_dt = to_date_dt.strftime("%d-%m-%Y")
            format_from_date_dt = from_date_dt.strftime("%d-%m-%Y")
            total_days = (to_date_dt - from_date_dt ).days + 1

            # comment below code new_app for test the email working or not
            new_app = Application.objects.create(
                user=user,
                leave_type_id=leave_type,
                request_form=request_form,
                from_date=from_date,
                to_date=to_date,
                total_days=total_days,
                remarks=remarks,
                status="Pending",
                entry_date=datetime.now()
            )
            # Email setup
            if auth_details and auth_details.get('auth_email_add'):
                leave_obj = LeaveType.objects.filter(id=leave_type).first()
                leave_name = leave_obj.name if leave_obj else ""

                # Assuming new_app is your Application instance
                change_url = reverse('admin:tickets_application_change', args=[new_app.id])
                # change_url = reverse('admin:tickets_application_change', args=[41])

                # Optional: add changelist filters (e.g., dep_head_status=Pending)
                filters = {
                    '_changelist_filters': urlencode({'dep_head_status': 'Pending'})
                }
                admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")
                # print(admin_link)
                # return JsonResponse({"admin_link": admin_link})
                context = {
                    "user_name": user.name.capitalize(),
                    "user_batch_number": user.batch_number,
                    "manager_name": auth_details.get('auth_name'),
                    "leave_type": leave_name,
                    "from_date": format_from_date_dt,
                    "to_date": format_to_date_dt,
                    "total_days": total_days,
                    "to_email": auth_details.get('auth_email_add'),
                    "admin_link": admin_link,
                }
                try:
                    email_data = send_application_email(template_type=1, context_data=context)
                    print(email_data)
                    return JsonResponse({"email_data": email_data})
                    if email_data:
                        new_app.email_sent = 1
                        new_app.save(update_fields=['email_sent'])
                except Exception as e:
                    print(f"Email sending failed: {e}")  # log but do not stop
            messages.success(request, f"Leave request submitted.")
        # Rejoining
        elif request_form_id == '2':
            app_id = request.POST.get('app_id')
            rejoin_date = request.POST.get('rejoin_date')
            application = Application.objects.filter(id=app_id, delete_status=False).first()
            if not application:
                return JsonResponse({"error": "Application not found"}, status=404)
            
            if application.rejoin_status:
                messages.warning(request, "Already applied rejoin request.")
            else:
                # Parse dates safely
                rejoin_dt = datetime.strptime(rejoin_date, "%Y-%m-%d").date()
                format_rejoin_dt = rejoin_dt.strftime("%d-%m-%Y")
                to_dt = application.to_date
                from_dt = application.from_date
                delay_days = 0
                if rejoin_dt > to_dt:
                    # Exclude the rejoin day itself
                    delay_days = (rejoin_dt - to_dt).days - 1
                    if delay_days < 0:
                        delay_days = 0 # prevent negative values

                total_days_after_rejoin = (rejoin_dt - from_dt).days
                # Create the new Rejoin application
                new_app = Application.objects.create(
                    user=user,
                    leave_type_id=6, 
                    request_form=request_form,
                    from_date=from_dt,
                    to_date=to_dt,
                    total_days=application.total_days,
                    remarks=application.remarks,
                    status="Pending",
                    entry_date=datetime.now(),
                    delayed_days=delay_days,
                    total_days_after_rejoin=total_days_after_rejoin,
                    rejoin_date=rejoin_dt,
                    application_id_rejoin=application.id,  # link back to original leave
                )
                # Update original leave application
                application.rejoin_status = 1
                application.application_id_rejoin = new_app.id
                application.save(update_fields=['rejoin_status', 'application_id_rejoin'])
                # Email setup
                if auth_details and auth_details.get('auth_email_add'):
                    # Assuming new_app is your Application instance
                    change_url = reverse('admin:tickets_application_change', args=[new_app.id])
                    # change_url = reverse('admin:tickets_application_change', args=[41])

                    # Optional: add changelist filters (e.g., dep_head_status=Pending)
                    filters = {
                        '_changelist_filters': urlencode({'dep_head_status': 'Pending'})
                    }
                    admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")
                    # print(admin_link)
                    # return JsonResponse({"admin_link": admin_link})
                    context = {
                        "user_name": user.name.capitalize(),
                        "user_batch_number": user.batch_number,
                        "manager_name": auth_details.get('auth_name'),
                        "rejoin_date": format_rejoin_dt,
                        "to_email": auth_details.get('auth_email_add'),
                        "admin_link": admin_link,
                    }
                    try:
                        email_data = send_application_email(template_type=2, context_data=context)
                        # print(email_data)
                        # return JsonResponse({"email_data": email_data})
                        if email_data:
                            new_app.email_sent = 1
                            new_app.save(update_fields=['email_sent'])
                    except Exception as e:
                        print(f"Email sending failed: {e}")  # log but do not stop
                
                messages.success(request, f"Rejoining request submitted.")
        # salary advance
        elif request_form_id == '3':
            month_id = request.POST.get('month')
            year_id = request.POST.get('year')
            remarks = request.POST.get('salary_ad_remarks')
            month = Month.objects.get(id=month_id) if month_id else None
            year = Year.objects.get(id=year_id) if year_id else None
            year_value = int(year.year)
            month_value = int(month.number) 
            first_day = date(year_value, month_value, 1)
            last_day = date(year_value, month_value, calendar.monthrange(year_value, month_value)[1])
            new_app = Application.objects.create(
                user=user,
                leave_type_id=7,
                request_form=request_form,
                salary_ad_month=month,
                salary_ad_year=year,
                remarks=remarks,
                from_date=first_day,
                to_date=last_day,
                status="Pending",
                entry_date=datetime.now()
            )
            # Email setup
            if auth_details and auth_details.get('auth_email_add'):
                    # Assuming new_app is your Application instance
                    change_url = reverse('admin:tickets_application_change', args=[new_app.id])
                    # change_url = reverse('admin:tickets_application_change', args=[41])

                    # Optional: add changelist filters (e.g., dep_head_status=Pending)
                    filters = {
                        '_changelist_filters': urlencode({'dep_head_status': 'Pending'})
                    }
                    admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")
                    # print(admin_link)
                    # return JsonResponse({"admin_link": admin_link})
                    context = {
                        "user_name": user.name.capitalize(),
                        "user_batch_number": user.batch_number,
                        "manager_name": auth_details.get('auth_name'),
                        "salary_ad_month": month,
                        "salary_ad_year": year,
                        "to_email": auth_details.get('auth_email_add'),
                        "admin_link": admin_link,
                    }
                    try:
                        email_data = send_application_email(template_type=3, context_data=context)
                        # print(email_data)
                        # return JsonResponse({"email_data": email_data})
                        if email_data:
                            new_app.email_sent = 1
                            new_app.save(update_fields=['email_sent'])
                    except Exception as e:
                        print(f"Email sending failed: {e}")  # log but do not stop

            messages.success(request, f"Salary Advance request submitted.")
            
        # clearance
        elif request_form_id == '4':
            # Save salary advance info
            pass

        return redirect('my_applications')
def my_applications(request):
    user_id = request.session.get('frontend_user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.get(id=user_id)
    applications = Application.objects.filter(user=user, delete_status=False).order_by('-entry_date')[:10]
    leave_types = LeaveType.objects.filter(status=1)
    request_forms = RequestForm.objects.filter(status=1)  # or whatever logic you use
    months = Month.objects.all()
    years = Year.objects.filter(status=1).order_by('year')

    # fetch last approved leave (not sick leave) for rejoining
    last_leave = (
        Application.objects.filter(
            user=user,
            status="Approved"
        )
        .exclude(leave_type__name__iexact="Sick Leave")
        .order_by("-to_date")
        .first()
    )


    return render(request, 'my_applications.html', {
        'applications': applications,
        'leave_types': leave_types,
        'request_forms': request_forms,  # for the apply form/modal
        'user': user,  # if you need to prefill user data
        'last_leave': last_leave,
        'months': months,
        'years': years,
    })

def edit_application(request, application_id):
    app = get_object_or_404(Application, id=application_id, delete_status=False)

    if app.status != 'Pending':
        return JsonResponse({'error': 'Only pending applications can be edited.'}, status=403)

    # Check request type
    request_type = app.request_form.id  # assuming FK to RequestForm model (id=1: Leave, id=2: Rejoining)
    email_sent = False
    new_app = None
    # Find Department Head email via department + name match
    user = User.objects.get(id=request.session.get('frontend_user_id'))
    auth_details = find_department_head_email(user)

    if request.method == 'POST':
        if request_type == 1:  # Leave
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            remarks = request.POST.get('remarks')
            leave_type_id = request.POST.get('leave_type')

            if not from_date or not to_date:
                return JsonResponse({'error': 'From Date and To Date are required.'})

            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
                to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
                format_to_date_dt = to_dt.strftime("%d-%m-%Y")
                format_from_date_dt = from_dt.strftime("%d-%m-%Y")
                total_days = (to_dt - from_dt).days + 1
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
            app.total_days = total_days
            app.save()
            # Email setup 
            if auth_details and auth_details.get('auth_email_add'):
                leave_obj = LeaveType.objects.filter(id=leave_type_id).first()
                leave_name = leave_obj.name if leave_obj else ""
                # Assuming new_app is your Application instance
                change_url = reverse('admin:tickets_application_change', args=[application_id])
                # change_url = reverse('admin:tickets_application_change', args=[41])

                # Optional: add changelist filters (e.g., dep_head_status=Pending)
                filters = {
                    '_changelist_filters': urlencode({'dep_head_status': 'Pending'})
                }
                admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")
                # print(admin_link)
                # return JsonResponse({"admin_link": admin_link})
                context = {
                    "user_name": user.name.capitalize(),
                    "user_batch_number": user.batch_number,
                    "manager_name": auth_details.get('auth_name'),
                    "leave_type": leave_name,
                    "from_date": format_from_date_dt,
                    "to_date": format_to_date_dt,
                    "total_days": total_days,
                    "to_email": auth_details.get('auth_email_add'),
                    "admin_link": admin_link,
                }
                try:
                    email_data = send_application_email(template_type=5, context_data=context)
                    print(email_data)
                    return JsonResponse({"email_data": email_data})
                    if email_data:
                        new_app.email_sent = 1
                        new_app.save(update_fields=['email_sent'])
                except Exception as e:
                    print(f"Email sending failed: {e}")  # log but do not stop

        elif request_type == 2:  # Rejoining
            rejoin_date = request.POST.get('rejoin_date')

            if not rejoin_date:
                return JsonResponse({'error': 'Rejoining Date is required.'})

            try:
                rejoin_dt = datetime.strptime(rejoin_date, "%Y-%m-%d").date()
                format_rejoin_dt = rejoin_dt.strftime("%d-%m-%Y")
            except ValueError:
                return JsonResponse({'error': 'Invalid date format. Please use YYYY-MM-DD.'})
            
            # linked leave application
            last_leave = None
            if app.application_id_rejoin:
                last_leave = Application.objects.filter(id=app.application_id_rejoin, delete_status=False).first()

            if not last_leave:
                return JsonResponse({'error': 'Linked leave application not found.'})

            to_dt = last_leave.to_date
            from_dt = last_leave.from_date

            # calculate delayed days (exclude rejoin day itself if late)
            delay_days = 0
            if rejoin_dt > to_dt:
                delay_days = (rejoin_dt - to_dt).days - 1
                if delay_days < 0:
                    delay_days = 0

            total_days_after_rejoin = (rejoin_dt - from_dt).days

            # update fields
            app.rejoin_date = rejoin_dt
            app.delayed_days = delay_days
            app.total_days_after_rejoin = total_days_after_rejoin
            app.save()
            # Email setup
            if auth_details and auth_details.get('auth_email_add'):
                    # Assuming new_app is your Application instance
                    change_url = reverse('admin:tickets_application_change', args=[application_id])
                    # change_url = reverse('admin:tickets_application_change', args=[41])

                    # Optional: add changelist filters (e.g., dep_head_status=Pending)
                    filters = {
                        '_changelist_filters': urlencode({'dep_head_status': 'Pending'})
                    }
                    admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")
                    # print(admin_link)
                    # return JsonResponse({"admin_link": admin_link})
                    context = {
                        "user_name": user.name.capitalize(),
                        "user_batch_number": user.batch_number,
                        "manager_name": auth_details.get('auth_name'),
                        "rejoin_date": format_rejoin_dt,
                        "to_email": auth_details.get('auth_email_add'),
                        "admin_link": admin_link,
                    }
                    try:
                        email_data = send_application_email(template_type=6, context_data=context)
                        # print(email_data)
                        # return JsonResponse({"email_data": email_data})
                        if email_data:
                            new_app.email_sent = 1
                            new_app.save(update_fields=['email_sent'])
                    except Exception as e:
                        print(f"Email sending failed: {e}")  # log but do not stop
        elif request_type == 3:  # Salary Advance
            month_id = request.POST.get('month')
            year_id = request.POST.get('year')
            remarks = request.POST.get('salary_ad_remarks')

            month = Month.objects.get(id=month_id) if month_id else None
            year = Year.objects.get(id=year_id) if year_id else None

            year_value = int(year.year)
            month_value = int(month.number) 

            first_day = date(year_value, month_value, 1)
            last_day = date(year_value, month_value, calendar.monthrange(year_value, month_value)[1])

            # update fields
            app.salary_ad_month = month
            app.salary_ad_year = year
            app.remarks = remarks
            app.from_date = first_day
            app.to_date = last_day
            app.save()
            # Email setup
            if auth_details and auth_details.get('auth_email_add'):
                    # Assuming new_app is your Application instance
                    change_url = reverse('admin:tickets_application_change', args=[application_id])
                    # change_url = reverse('admin:tickets_application_change', args=[41])

                    # Optional: add changelist filters (e.g., dep_head_status=Pending)
                    filters = {
                        '_changelist_filters': urlencode({'dep_head_status': 'Pending'})
                    }
                    admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")
                    # print(admin_link)
                    # return JsonResponse({"admin_link": admin_link})
                    context = {
                        "user_name": user.name.capitalize(),
                        "user_batch_number": user.batch_number,
                        "manager_name": auth_details.get('auth_name'),
                        "salary_ad_month": month,
                        "salary_ad_year": year,
                        "to_email": auth_details.get('auth_email_add'),
                        "admin_link": admin_link,
                    }
                    try:
                        email_data = send_application_email(template_type=7, context_data=context)
                        # print(email_data)
                        # return JsonResponse({"email_data": email_data})
                        if email_data:
                            new_app.email_sent = 1
                            new_app.save(update_fields=['email_sent'])
                    except Exception as e:
                        print(f"Email sending failed: {e}")  # log but do not stop

        else:
            return JsonResponse({'error': 'Unsupported request type.'}, status=400)

        return JsonResponse({'success': True})

    # GET request → return correct modal template
    if request_type == 1:  # Leave
        leave_types = LeaveType.objects.filter(status=1, request_form=app.request_form)
        app.from_date_display = app.from_date.strftime("%Y-%m-%d") if app.from_date else ""
        app.to_date_display = app.to_date.strftime("%Y-%m-%d") if app.to_date else ""
        html = render_to_string(
            'partials/edit_application_modal.html',
            {'application': app, 'leave_types': leave_types},
            request=request
        )
    elif request_type == 2:  # Rejoining
        app.rejoin_date_display = app.rejoin_date.strftime("%Y-%m-%d") if app.rejoin_date else ""
        # fetch the leave application linked via application_id_rejoin
        last_leave = None
        if app.application_id_rejoin:
            try:
                last_leave = Application.objects.get(id=app.application_id_rejoin)
            except Application.DoesNotExist:
                last_leave = None
        html = render_to_string(
            'partials/edit_rejoin_modal.html',
            {'application': app,'last_leave': last_leave,},
            request=request
        )
    elif request_type == 3:  # Salary Advance
        months = Month.objects.all()
        years = Year.objects.filter(status=1).order_by('year')
        html = render_to_string(
            'partials/edit_salary_ad_modal.html',
            {'application': app,'months': months,'years': years,},
            request=request
        )
    else:
        return JsonResponse({'error': 'Unsupported request type.'}, status=400)

    return HttpResponse(html)

@require_POST
def delete_application(request, application_id):
    app = get_object_or_404(Application, id=application_id)

    if app.status != 'Pending':
        return JsonResponse({'error': 'Only pending applications can be marked deleted.'}, status=403)

    request_type = app.request_form.id  # 1 = Leave, 2 = Rejoining

    if request_type == 2:  # Rejoining
        # app.application_id_rejoin points to the original leave
        if app.application_id_rejoin:
            try:
                leave_app = Application.objects.get(id=app.application_id_rejoin, delete_status=False)
                leave_app.rejoin_status = 0
                leave_app.application_id_rejoin = None
                leave_app.save(update_fields=['rejoin_status', 'application_id_rejoin'])
            except Application.DoesNotExist:
                pass  # if leave not found, just ignore

        # Now delete the rejoin application itself
        app.delete()

    else:
        app.delete()

    return JsonResponse({'success': True})
    
def custom_logout(request):
    logout(request)
    return render(request, "admin/logged_out.html")

def change_password(request):
    user_id = request.session.get('frontend_user_id')
    user = User.objects.get(id=user_id, status=1)
    if not user_id:
        return redirect('login')
    
    if request.method == "POST":
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        # Match new/confirm password
        if new_password != confirm_password:
            return JsonResponse({'status': 'error', 'message': 'New password and confirm password do not match.'})

        # Check current password
        if user.password.strip() != current_password:
            return JsonResponse({'status': 'error', 'message': 'Current password is incorrect.'})

        # Update password (no hashing as per your request)
        user.password = new_password
        user.save()

        return JsonResponse({'status': 'success', 'message': 'Password updated successfully.'})

    return render(request, 'change_password.html',{'user': user})

def download_application(request, app_id,req_id):

    logo_url = request.build_absolute_uri(static('images/awc-logo.jpg'))
    boostrap_url = request.build_absolute_uri(static('css/bootstrap.min.css'))
    application_leave_url = request.build_absolute_uri(static('css/application_leave.css'))
    favicon_url = request.build_absolute_uri(static('images/favicon.ico'))
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

    if req_id == 1:
        application = get_object_or_404(Application, id=app_id)
        html = render_to_string("application_leave.html", {
            "application": application,
            "today": date.today(),
            "logo_url": logo_url,
            "boostrap_url": boostrap_url,
            "application_leave_url": application_leave_url,
            "favicon_url": favicon_url,
        })

        
        options = {
            'enable-local-file-access': '',
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'margin-top': '35mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'margin-right': '20mm',
            'zoom': '1.0',  # keep content at actual size
        }

        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        response = HttpResponse(pdf,content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Application_{application.application_id}.pdf"'
        return response
    elif req_id == 2: 
        application = get_object_or_404(Application, id=app_id)
        html = render_to_string("application_rejoin.html", {
            "application": application,
            "today": date.today(),
            "logo_url": logo_url,
            "boostrap_url": boostrap_url,
            "application_leave_url": application_leave_url,
            "favicon_url": favicon_url,
        })

        options = {
            'enable-local-file-access': '',
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'margin-top': '35mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'margin-right': '20mm',
            'zoom': '1.0',  # keep content at actual size
        }

        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        response = HttpResponse(pdf,content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Application_{application.application_id}.pdf"'
        return response
    elif req_id == 3: 
        application = get_object_or_404(Application, id=app_id)
        html = render_to_string("application_salary_ad.html", {
            "application": application,
            "today": date.today(),
            "logo_url": logo_url,
            "boostrap_url": boostrap_url,
            "application_leave_url": application_leave_url,
            "favicon_url": favicon_url,
        })

        options = {
            'enable-local-file-access': '',
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'margin-top': '35mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'margin-right': '20mm',
            'zoom': '1.0',  # keep content at actual size
        }

        pdf = pdfkit.from_string(html, False, configuration=config, options=options)
        response = HttpResponse(pdf,content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Application_{application.application_id}.pdf"'
        return response
    
    

def print_application(request, app_id, req_id):
    # get session user id
    user_id = request.session.get('frontend_user_id')

    if not user_id:  
        return redirect('login')  # not logged in
    
    logo_url = request.build_absolute_uri(static('images/awc-logo.jpg'))
    boostrap_url = request.build_absolute_uri(static('css/bootstrap.min.css'))
    application_leave_url = request.build_absolute_uri(static('css/application_leave.css'))
    favicon_url = request.build_absolute_uri(static('images/favicon.ico'))

    if req_id == 1:
        # filter by app_id + req_id + user_id
        application = Application.objects.filter(
            id=app_id,
            request_form=req_id,
            user=user_id   # use user_id directly
        ).first()

        if application:
            return render(request, "application_leave.html", {
                "application": application,
                "today": date.today(),
                "logo_url": logo_url,
                "boostrap_url": boostrap_url,
                "application_leave_url": application_leave_url,
                "favicon_url": favicon_url,
            })
        else:
            return render(request, "application_not_found.html")
    elif req_id == 2:
        # filter by app_id + req_id + user_id
        application = Application.objects.filter(
            id=app_id,
            request_form=req_id,
            user=user_id   # use user_id directly
        ).first()

        if application:
            return render(request, "application_rejoin.html", {
                "application": application,
                "today": date.today(),
                "logo_url": logo_url,
                "boostrap_url": boostrap_url,
                "application_leave_url": application_leave_url,
                "favicon_url": favicon_url,
            })
        else:
            return render(request, "application_not_found.html")
    elif req_id == 3:
        # filter by app_id + req_id + user_id
        application = Application.objects.filter(
            id=app_id,
            request_form=req_id,
            user=user_id   # use user_id directly
        ).first()

        if application:
            return render(request, "application_salary_ad.html", {
                "application": application,
                "today": date.today(),
                "logo_url": logo_url,
                "boostrap_url": boostrap_url,
                "application_leave_url": application_leave_url,
                "favicon_url": favicon_url,
            })
        else:
            return render(request, "application_not_found.html")
    else:
        return redirect('login')
def get_leave_types(request, req_id):
    leave_types = LeaveType.objects.filter(
        status=1,
        request_form_id=req_id
    ).values("id", "name")

    return JsonResponse(list(leave_types), safe=False)

def email_test(request):
    context = {
        "user_name": "Amerish N",
        "manager_name": "John Doe",
        "from_date": "2025-10-14",
        "to_date": "2025-10-16",
        "total_days": 3,
        "to_email": "amerish@watancon.com",
    }

    success = send_application_email(1, context)
    return JsonResponse({"status": "sent" if success else "failed"}) 
    # ---------------------- Testing mail-----------------------------------------------
    # try:
    #     socket.setdefaulttimeout(15)  # timeout in 5 seconds

    #     s = EmailSettings.objects.first()
    #     print("SMTP HOST:", s.smtp_host)
    #     print("SMTP PORT:", s.smtp_port)

    #     conn = get_connection(
    #         host=s.smtp_host,
    #         port=s.smtp_port,
    #         username=s.smtp_user,
    #         password=s.smtp_pass,
    #         use_tls=True,
    #         timeout=5,  # <-- important
    #     )

    #     send_mail(
    #         subject="Test Email",
    #         message="This is a plain test",
    #         from_email=s.from_email,
    #         recipient_list=["amerish@watancon.com"],
    #         connection=conn,
    #         fail_silently=False,
    #     )

    #     return JsonResponse({"status": "sent"})

    # except Exception as e:
    #     import traceback
    #     return JsonResponse({
    #         "status": "failed",
    #         "error": str(e),
    #         "trace": traceback.format_exc()
    #     })