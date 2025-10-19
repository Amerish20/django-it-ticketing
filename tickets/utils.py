from .models import DepartmentHead,EmailSettings,EmailTemplate,LeaveType,Month, Year
from django.contrib.auth.models import User, Group
from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives,EmailMessage,get_connection,send_mail
from django.utils.html import strip_tags
from django.http import JsonResponse
import socket
from django.urls import reverse
from urllib.parse import urlencode

def is_same_department(user, employee_department_id):
    """
    Check if the logged-in user is DepartmentHead of the employee's department.
    Returns 1 if same department, else 0.
    """
    user_departments = DepartmentHead.objects.filter(
        auth_user=user, status=1
    ).values_list("department_id", flat=True)

    return 1 if employee_department_id in user_departments else 0

def send_application_email(template_type, context_data):
    # print(context_data)
    # return JsonResponse({"debug_context_data": context_data})
    try:
        # Get active email settings
        email_settings = EmailSettings.objects.filter(status=True).first()
        if not email_settings:
            raise Exception("No active email settings found.")
        print("Using SMTP host:", email_settings.smtp_host)
        # Get email template
        template = EmailTemplate.objects.filter(template_type=template_type, status=True).first()
        if not template:
            raise Exception(f"No template found.")
        
        # Render subject and body using placeholders
        subject = Template(template.subject).render(Context(context_data))
        html_body = Template(template.body).render(Context(context_data))
        text_body = strip_tags(html_body)
        print(text_body)
        return JsonResponse({"text_body": text_body})
        # Create custom connection to test SMTP
        connection = get_connection(
            host=email_settings.smtp_host,
            port=email_settings.smtp_port,
            username=email_settings.smtp_user,
            password=email_settings.smtp_pass,
            use_tls=True,
            fail_silently=False
        )
        print("SMTP Connection created")
        # Send email
        email = EmailMessage(
            subject=subject,
            body=text_body,
            from_email=f"{email_settings.from_name} <{email_settings.from_email}>",
            to=[context_data.get("to_email")]
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)

        print("Email sent successfully")
        return True

    except Exception as e:
        import traceback
        print(f"Email sending failed: {e}")
        print(traceback.format_exc())  # Full error traceback
        return False

def find_department_head_email(custom_user):
    """
    Find department head email based on the user's department.
    Uses the DepartmentHead model which links directly to AuthUser.
    """
    if not custom_user.department:
        return None

    # Find department head for the same department (active one)
    dep_head = DepartmentHead.objects.filter(
        department=custom_user.department,
        status=1
    ).select_related('auth_user').first()

    if not dep_head:
        return None

    auth_user = dep_head.auth_user
    name = auth_user.username.capitalize()
    email = auth_user.email.lower()
    if not email:
        return None

    return {
        "auth_name": name,
        "auth_email_add": email
    }

def send_application_email_admin(template_type, context_data, context_other_data):
    try:
        # Get active email settings
        email_settings = EmailSettings.objects.filter(status=True).first()
        if not email_settings:
            raise Exception("No active email settings found.")
        print("Using SMTP host:", email_settings.smtp_host)

        # Get email template
        template = EmailTemplate.objects.filter(template_type=template_type, status=True).first()
        if not template:
            raise Exception(f"No template found.")
        
        # Create custom connection to test SMTP
        connection = get_connection(
            host=email_settings.smtp_host,
            port=email_settings.smtp_port,
            username=email_settings.smtp_user,
            password=email_settings.smtp_pass,
            use_tls=True,
            fail_silently=False
        )
        print("SMTP Connection created")

        # Send email
        if context_data:
            subject_context_data = Template(template.subject).render(Context(context_data))
            html_body_context_data = Template(template.body).render(Context(context_data))
            text_body_context_data = strip_tags(html_body_context_data)
            print(text_body_context_data)
            # exit()
            # email = EmailMessage(
            #     subject=subject_context_data,
            #     body=text_body_context_data,
            #     from_email=f"{email_settings.from_name} <{email_settings.from_email}>",
            #     to=[context_data.get("to_email")]
            # )
            # email.content_subtype = "html"
            # email.send(fail_silently=False)
        else:
            context_data = None

        if context_other_data:
            subject_context_other_data = Template(template.subject).render(Context(context_other_data))
            html_body_context_other_data = Template(template.body).render(Context(context_other_data))
            text_body_context_other_data = strip_tags(html_body_context_other_data)
            print(text_body_context_other_data)
            # exit()
            # email_other = EmailMessage(
            #     subject=subject_context_other_data,
            #     body=text_body_context_other_data,
            #     from_email=f"{email_settings.from_name} <{email_settings.from_email}>",
            #     to=[context_data.get("to_email")]
            # )
            # email_other.content_subtype = "html"
            # email_other.send(fail_silently=False)
        else:
            context_other_data = None
        
        print("Email sent successfully")
        return True

    except Exception as e:
        import traceback
        print(f"Email sending failed: {e}")
        print(traceback.format_exc())  # Full error traceback
        return False
    
def email_for_application(obj, request, action_type):
    # print(f"action_type: {action_type}")
    # exit()
    # Admin URL for reference
    change_url = reverse('admin:tickets_application_change', args=[obj.id])
    filters = {'_changelist_filters': urlencode({'dep_head_status': 'Pending'})}
    admin_link = request.build_absolute_uri(f"{change_url}?{filters['_changelist_filters']}")

    # Extract user name safely
    user_name = str(obj.user)
    user_sent_user_name = str(obj.user).split("-")[0].strip().capitalize()
    manager_name = str(request.user).capitalize()

    # Get application user email if available
    user_email = getattr(obj.user, "user_email", None)

    # Get  Group users 
    if request.user.groups.filter(name__in=['DepartmentHead']).exists():
        auth_group = Group.objects.filter(name="HR").first()
        auth_user = User.objects.filter(groups=auth_group).first()
        if obj.gm_status != 'Approved':
            auth_user_email = auth_user.email
        else:
            auth_user_email = None
        auth_user_name = auth_user.username
        auth_sent_user_name = str(auth_user_name).capitalize()
    elif request.user.groups.filter(name__in=['HR']).exists():
        auth_group = Group.objects.filter(name="GM").first()
        auth_user = User.objects.filter(groups=auth_group).first()
        if obj.gm_status != 'Approved':
            auth_user_email = auth_user.email
        else:
            auth_user_email = None
        auth_user_name = auth_user.username
        auth_sent_user_name = str(auth_user_name).capitalize()
    elif request.user.groups.filter(name__in=['GM']).exists():
        if obj.hr_status == "Pending" and action_type == 'Approved':
            auth_group = Group.objects.filter(name="HR").first()
            auth_user = User.objects.filter(groups=auth_group).first()
            auth_user_email = auth_user.email
            auth_user_name = auth_user.username
            auth_sent_user_name = str(auth_user_name).capitalize()
        else:
            auth_user_email = None

    # Leave request type
    if obj.request_form_id == 1:
        leave_obj = LeaveType.objects.filter(id=obj.leave_type_id).first()
        leave_name = leave_obj.name if leave_obj else ""

        # Format dates
        format_to_date_dt = obj.to_date.strftime("%d-%m-%Y")
        format_from_date_dt = obj.from_date.strftime("%d-%m-%Y")

        # Build email context
        # For User
        if user_email:
            context = {
                "sent_user": user_sent_user_name,
                "user_name": user_name,
                "manager_name": manager_name,
                "leave_type": leave_name,
                "from_date": format_from_date_dt,
                "to_date": format_to_date_dt,
                "total_days": obj.total_days,
                "to_email": user_email,  
                "admin_link": admin_link,
                "show_next_level": False
            }
        else:
            context = None
        # For Group Head
        if request.user.groups.filter(name__in=['DepartmentHead']).exists() or request.user.groups.filter(name__in=['HR']).exists() or request.user.groups.filter(name__in=['GM']).exists():
            if auth_user_email:
                context_other = {
                    "sent_user": auth_sent_user_name,
                    "user_name": user_name,
                    "manager_name": manager_name,
                    "leave_type": leave_name,
                    "from_date": format_from_date_dt,
                    "to_date": format_to_date_dt,
                    "total_days": obj.total_days,
                    "to_email": auth_user_email,  
                    "admin_link": admin_link,
                    "show_next_level": True
                }
            else:
                context_other = None
    
        # print("Email Context:", context)
        # print("Email Context Others:", context_other)
        # exit()

        if action_type == 'Approved':
            template_type_id = 9
        else:
            context_other = None
            template_type_id = 10

    # Rejoining
    if obj.request_form_id == 2:
        # Rejoin dates
        format_rejoin_dt = obj.rejoin_date.strftime("%d-%m-%Y")
        
        # Build email context
        # For User
        if user_email:
            context = {
                "sent_user": user_sent_user_name,
                "user_name": user_name,
                "manager_name": manager_name,
                "rejoin_date": format_rejoin_dt,
                "to_email": user_email,  
                "admin_link": admin_link,
                "show_next_level": False
            }
        else:
            context = None
        # For Group Head
        if request.user.groups.filter(name__in=['DepartmentHead']).exists() or request.user.groups.filter(name__in=['HR']).exists() or request.user.groups.filter(name__in=['GM']).exists():
            if auth_user_email:
                context_other = {
                    "sent_user": auth_sent_user_name,
                    "user_name": user_name,
                    "manager_name": manager_name,
                    "rejoin_date": format_rejoin_dt,
                    "to_email": auth_user_email,  
                    "admin_link": admin_link,
                    "show_next_level": True
                }
            else:
                context_other = None
        else:
            context_other = None

        # print("Email Context:", context)
        # print("Email Context Others:", context_other)
        # exit()

        if action_type == 'Approved':
            template_type_id = 11
        else:
            context_other = None
            template_type_id = 12

    # salary advance
    if obj.request_form_id == 3:
        # month and year 
        month = Month.objects.get(id=obj.salary_ad_month_id)
        year = Year.objects.get(id=obj.salary_ad_year_id)
        
        # Build email context
        # For User
        if user_email:
            context = {
                "sent_user": user_sent_user_name,
                "user_name": user_name,
                "manager_name": manager_name,
                "salary_ad_month": month,
                "salary_ad_year": year,
                "to_email": user_email,  
                "admin_link": admin_link,
                "show_next_level": False
            }
        else:
            context = None
        # For Group Head
        if request.user.groups.filter(name__in=['DepartmentHead']).exists() or request.user.groups.filter(name__in=['HR']).exists() or request.user.groups.filter(name__in=['GM']).exists():
            if auth_user_email:
                context_other = {
                    "sent_user": auth_sent_user_name,
                    "user_name": user_name,
                    "manager_name": manager_name,
                    "salary_ad_month": month,
                    "salary_ad_year": year,
                    "to_email": auth_user_email,  
                    "admin_link": admin_link,
                    "show_next_level": True
                }
            else:
                context_other = None
        else:
            context_other = None

        # print("Email Context:", context)
        # print("Email Context Others:", context_other)
        # exit()

        if action_type == 'Approved':
            template_type_id = 13
        else:
            context_other = None
            template_type_id = 14


    try:
        email_data = send_application_email_admin(template_type=template_type_id, context_data=context,context_other_data=context_other)
        print(email_data)
        return JsonResponse({"email_data": email_data})
    except Exception as e:
        print(f"Email sending failed: {e}")

