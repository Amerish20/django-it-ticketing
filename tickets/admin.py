from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from django.templatetags.static import static
from django.shortcuts import render,get_object_or_404
from django.utils.html import format_html
from xhtml2pdf import pisa
import datetime
import calendar
import csv
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.contrib.admin.sites import site as admin_site
from .forms import ApplicationAdminForm
from django.db.models import Q
from django.contrib.admin.views.main import ChangeList
from .utils import is_same_department,email_for_application
from django.contrib import messages
import pdfkit
from .models import (
    User, Ticket, Department, Designation, Item, Inventory,
    InventoryItem, InventoryReport, RequestForm, LeaveType,
    Nationality, DepartmentHead, Application, Year,EmailTemplate,EmailSettings,EmailTemplateType
)
from django import forms

admin.site.site_header = "Welcome to Al Wataniya Concrete Admin Portal"
admin.site.site_title = "Al Wataniya Concrete – Admin Portal"
admin.site.index_title = "Welcome to Al Wataniya Concrete Admin Portal"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    # Action to mark selected departments inactive
    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} departments marked as inactive.")
    mark_inactive.short_description = "Mark selected departments as inactive"

    # Action to mark selected departments active
    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} departments marked as active.")
    mark_active.short_description = "Mark selected departments as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} item marked as inactive.")
    mark_inactive.short_description = "Mark selected item as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} item marked as active.")
    mark_active.short_description = "Mark selected item as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} designation as inactive.")
    mark_inactive.short_description = "Mark selected designation as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} designation marked as active.")
    mark_active.short_description = "Mark selected designation as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(Nationality)
class NationalityAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} nationality as inactive.")
    mark_inactive.short_description = "Mark selected nationality as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} nationality marked as active.")
    mark_active.short_description = "Mark selected nationality as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'batch_number',
        'password',
        'status',
        'department',
        'designation',
        'mobile_number',
        'qid',
        'qid_expiry_date',
        'nationality',
        'passport_number',
        'passport_expiry_date',
        'marital_status',
        
    )
    list_filter = (
        'department', 'status','nationality','designation'
    )
    search_fields = ('name', 'batch_number')
    list_per_page = 20

    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} user marked as inactive.")
    mark_inactive.short_description = "Mark selected user as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} user marked as active.")
    mark_active.short_description = "Mark selected user as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "department":
            kwargs["queryset"] = Department.objects.filter(status=1)  # Only active departments
        elif db_field.name == "nationality":
            kwargs["queryset"] = Nationality.objects.filter(status=1)  # Only active nationalities
        elif db_field.name == "designation":
            kwargs["queryset"] = Designation.objects.filter(status=1)  # Only active designations
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Hide password column from the list view for non-superusers
    def get_list_display(self, request):
        list_display = list(super().get_list_display(request))
        if not request.user.is_superuser:
            if 'password' in list_display:
                list_display.remove('password')
        return list_display

    # Hide password field when editing an existing user
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            if obj:  # Editing an existing user
                new_fieldsets = []
                for name, opts in fieldsets:
                    fields = list(opts.get('fields', []))
                    if 'password' in fields:
                        fields.remove('password')
                    new_fieldsets.append((name, {'fields': fields}))
                return new_fieldsets
        return fieldsets

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id','user_name', 'user_batch_number', 'user_department', 'item', 'status', 'request_date')
    list_filter = ('status', 'item', 'user__department')
    search_fields = ('user__name', 'user__batch_number', 'item__name', 'description')
    list_per_page = 20

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(status=1)  # Only active users
        elif db_field.name == "item":
            kwargs["queryset"] = Item.objects.filter(status=1)  # Only active items
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def user_name(self, obj): return obj.user.name
    def user_batch_number(self, obj): return obj.user.batch_number
    def user_department(self, obj): return obj.user.department.name if obj.user.department else '—'

    user_name.short_description = 'User'
    user_batch_number.short_description = 'Batch Number'
    user_department.short_description = 'Department'


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('inventory_id','name', 'manufacturer', 'serial_number', 'asset_code', 'buy_date', 'status')
    list_filter = ('status',)
    search_fields = ('inventory_id','name', 'serial_number', 'asset_code')
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} inventory item marked as inactive.")
    mark_inactive.short_description = "Mark selected inventory item as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} inventory item marked as active.")
    mark_active.short_description = "Mark selected inventory item as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        'inventory_item', 'user', 'issue_date', 'return_date', 'entry_date',
         'status', 'inventory_status', 'print_pdf_link',
    )
    list_filter = ('inventory_item', 'user', 'department', 'issue_date', 'return_date', 'status', 'inventory_status')
    search_fields = (
        'inventory_item__serial_number', 'inventory_item__name',
        'user__name',
    )
    list_per_page = 20
    actions = ['generate_combined_pdf','mark_inactive', 'mark_active']


    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} inventory marked as inactive.")
    mark_inactive.short_description = "Mark selected inventory as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} inventory marked as active.")
    mark_active.short_description = "Mark selected inventory as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "inventory_item":
            kwargs["queryset"] = InventoryItem.objects.filter(status=1) 
        elif db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(status=1)  
        elif db_field.name == "department":
            kwargs["queryset"] = Department.objects.filter(status=1)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def print_pdf_link(self, obj):
        url = reverse('admin:print_inventory_pdf', args=[obj.pk])
        return format_html('<a class="button" target="_blank" href="{}">Print PDF</a>', url)
    print_pdf_link.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('print-inventory/<int:pk>/', self.admin_site.admin_view(self.print_inventory_pdf), name='print_inventory_pdf'),
            path('inventory-report/', self.admin_site.admin_view(inventory_report_view), name='inventory_report'),
        ]
        return custom_urls + urls

    def print_inventory_pdf(self, request, pk):
        inventory = Inventory.objects.get(pk=pk)
        logo_url = request.build_absolute_uri(static('images/awc-logo.jpg'))

        html = render_to_string('admin/inventory_print.html', {
            'inventories': [inventory],
            'user': inventory.user,
            'company_name': "Al Wataniya Concrete",
            'today': datetime.date.today(),
            'logo_url': logo_url,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="inventory_{pk}.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    def generate_combined_pdf(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "No inventory items selected.", level='warning')
            return
        
        # Determine if all inventories belong to the same user
        users = set(inv.user for inv in queryset)
        user = users.pop() if len(users) == 1 else None  # Only one user will be shown

        logo_url = request.build_absolute_uri(static('images/favicon.ico'))
        html = render_to_string('admin/inventory_print.html', {
            'inventories': queryset,
            'user': user,  # pass user if single user only
            'company_name': "Al Wataniya Concrete",
            'today': datetime.date.today(),
            'logo_url': logo_url,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventory_combined.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    generate_combined_pdf.short_description = "Print selected inventory as PDF"


def inventory_report_view(request):
    # fetch your data
    users = User.objects.all()
    departments = Department.objects.all()
    inventories = Inventory.objects.all()
    items = InventoryItem.objects.all()

    selected_user = request.GET.get('user')
    selected_department = request.GET.get('department')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    export = request.GET.get('export')
    selected_item = request.GET.get('inventory_item')

    if selected_user:
        inventories = inventories.filter(user_id=selected_user)
    if selected_department:
        inventories = inventories.filter(department_id=selected_department)
    if from_date:
        inventories = inventories.filter(issue_date__gte=parse_date(from_date))
    if to_date:
        inventories = inventories.filter(issue_date__lte=parse_date(to_date))
    if selected_item:
        inventories = inventories.filter(inventory_item_id=selected_item)

    if export == 'pdf':
        logo_url = request.build_absolute_uri(static('images/favicon.ico'))
        selected_user_obj = User.objects.filter(id=selected_user).first() if selected_user else None
        html = render_to_string('admin/inventory_report_pdf.html', {
            'inventories': inventories,
            'today': datetime.date.today(),
            'company_name': 'Al Wataniya Concrete',
            'logo_url': logo_url,
            'user': selected_user_obj,
            'multiple_users': not selected_user,
        })
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'
        pisa.CreatePDF(html, dest=response)
        return response

    if export == 'excel':
        selected_user_obj = User.objects.filter(id=selected_user).first() if selected_user else None

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
        writer = csv.writer(response)

        if selected_user_obj:
            writer.writerow(['User Info'])
            writer.writerow([
                f'Name: {selected_user_obj.name}',
                f'Batch Number: {selected_user_obj.batch_number}',
                f'Department: {selected_user_obj.department.name if selected_user_obj.department else ""}',
                f'Mobile Number: {selected_user_obj.mobile_number if selected_user_obj.mobile_number else ""}'
            ])
            writer.writerow([])

            writer.writerow([
                '#', 'Item Name', 'Serial No', 'Asset Code',
                'Issue Date', 'User Sign', 'Return Date', 'Remarks'
            ])
            for idx, inv in enumerate(inventories, 1):
                writer.writerow([
                    idx,
                    inv.inventory_item.name,
                    inv.inventory_item.serial_number,
                    inv.inventory_item.asset_code,
                    inv.issue_date,
                    '',
                    inv.return_date or '',
                    inv.remarks or ''
                ])
        else:
            writer.writerow([
                '#', 'User Name', 'Batch Number', 'Department',
                'Item Name', 'Serial No', 'Asset Code',
                'Issue Date', 'User Sign', 'Return Date', 'Remarks'
            ])
            for idx, inv in enumerate(inventories, 1):
                writer.writerow([
                    idx,
                    inv.user.name,
                    inv.user.batch_number,
                    inv.user.department.name if inv.user.department else '',
                    inv.inventory_item.name,
                    inv.inventory_item.serial_number,
                    inv.inventory_item.asset_code,
                    inv.issue_date,
                    '',
                    inv.return_date or '',
                    inv.remarks or ''
                ])
        return response


    # Inject admin context
    context = dict(
        admin_site.each_context(request),  # brings admin header, user info, etc.
        users=users,
        departments=departments,
        items=items,
        inventories=inventories,
    )
    return render(request, 'admin/inventory_report.html', context)


@admin.register(InventoryReport)
class ReportAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse('admin:inventory_report'))

@admin.register(RequestForm)
class RequestFormAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 20

    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} request form marked as inactive.")
    mark_inactive.short_description = "Mark selected request form as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} request form marked as active.")
    mark_active.short_description = "Mark selected request form as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name','request_form', 'status')
    list_filter = ('status',)
    search_fields = ('name',)
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} leave type marked as inactive.")
    mark_inactive.short_description = "Mark selected departments head as inactive"

    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} leave type marked as active.")
    mark_active.short_description = "Mark selected departments head as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

@admin.register(DepartmentHead)
class DepartmentHeadAdmin(admin.ModelAdmin):
    list_display = ('id','department','auth_user', 'status')
    list_filter = ('status', 'department')
    search_fields = ('auth_user__username', 'department__name')
    list_per_page = 20
    actions = ['mark_inactive', 'mark_active']

    # Action to mark selected departments inactive
    def mark_inactive(self, request, queryset):
        updated = queryset.update(status=0)
        self.message_user(request, f"{updated} departments head marked as inactive.")
    mark_inactive.short_description = "Mark selected departments head as inactive"

    # Action to mark selected departments active
    def mark_active(self, request, queryset):
        updated = queryset.update(status=1)
        self.message_user(request, f"{updated} departments head marked as active.")
    mark_active.short_description = "Mark selected departments head as active"

    # Remove default delete_selected action
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "department":
            kwargs["queryset"] = Department.objects.filter(status=1)  # Only active departments
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ('year', 'status')
    list_editable = ('status',)
    ordering = ('year',)
    search_fields = ('year',)

@admin.register(EmailTemplateType)
class EmailTemplateTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('name',)
    ordering = ('id',)

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'template_type', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('name', 'template_type__name', 'subject')
    ordering = ('id',)
    autocomplete_fields = ['template_type']  # useful if you have many template types


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_name', 'from_email', 'smtp_host', 'smtp_user', 'smtp_port', 'status')
    list_filter = ('status',)
    search_fields = ('from_name', 'from_email', 'smtp_host', 'smtp_user')
    ordering = ('id',)

class SimpleDropdownFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return [
            ("Pending", "Pending"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
        ]
    
    def choices(self, changelist):
        # Skip the "All" option
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(**{self.parameter_name: self.value()})
        return queryset


class DepHeadStatusFilter(SimpleDropdownFilter):
    title = "Dep Head Status"
    parameter_name = "dep_head_status"


class HRStatusFilter(SimpleDropdownFilter):
    title = "HR Status"
    parameter_name = "hr_status"


class GMStatusFilter(SimpleDropdownFilter):
    title = "GM Status"
    parameter_name = "gm_status"

class LeaveTypeFilter(admin.SimpleListFilter):
    title = 'Type'  # 👈 This changes the filter label
    parameter_name = 'leave_type'

    def lookups(self, request, model_admin):
        leave_types = LeaveType.objects.all()
        return [(lt.id, lt.name) for lt in leave_types]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(leave_type_id=self.value())
        return queryset

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    
    all_fields = (
        'application_id',
        'user_batch_number',
        'user_name',
        'user_department',
        'display_leave_type',
        'remarks',
        'colored_status',
        'from_date',
        'to_date',
        'rejoin_date',
        'display_month',
        'display_year',
        'display_total_days',
        'delayed_days',
        'remarks_dep_head',
        'dep_head_status_display',
        'remarks_hr',
        'hr_status_display',
        'remarks_gm',
        'gm_status_display',
        'entry_date',
        'download_button',
    )

    limited_fields = (
        'application_id',
        'user_batch_number',
        'user_name',
        'user_department',
        'display_leave_type',
        'remarks',
        'from_date',
        'to_date',
        'rejoin_date',
        'display_month',
        'display_year',
        'display_total_days',
        'delayed_days',
        'colored_status',
        'download_button',
    )

    list_per_page = 10
    base_filters  = (
        LeaveTypeFilter,
        'from_date',
        'to_date',
    )
    search_fields = (
        'application_id',
        'user__name', 'user__batch_number',
        'leave_type__name',
        'dep_head_status', 'hr_status', 'gm_status'
    )

    actions = [
        'approve_stage', 'reject_stage', 'soft_delete_selected'
    ]

    exclude = ('delete_status',)

    def has_add_permission(self, request):
        return False


    def display_total_days(self, obj):
        return obj.total_days_after_rejoin if obj.total_days_after_rejoin else obj.total_days
    display_total_days.short_description = "Total Days"

    def display_month(self, obj):
        return obj.salary_ad_month if obj.salary_ad_month else None
    display_month.short_description = "Month"

    def display_year(self, obj):
        return obj.salary_ad_year if obj.salary_ad_year else None
    display_year.short_description = "Year"

    def display_leave_type(self, obj):
        # Check request type (assuming 1 = Leave, 2 = Rejoining)
        if obj.request_form_id == 2:  
            color = "#9ecaf9"  # light blue for rejoining
            text = "Rejoining"
        elif obj.request_form_id == 3:
            color = "#f79ec4"  # light blue for salary advance
            text = "Salary Advance"
        else:
            # For all other leave types, single color (light green for example)
            color = "#a4f5b8"
            text = obj.leave_type.name if obj.leave_type else "N/A"

        return format_html(
            '<span style="background-color:{}; padding:4px 8px; border-radius:4px; display:inline-block;font-weight:bold;">{}</span>',
            color, text
        )
    
    display_leave_type.short_description = "Type"

    def download_button(self, obj):
        url = reverse('admin:download_application_admin', args=[obj.id, obj.request_form_id])
        return format_html('<a class="button" target="_blank" href="{}">Download</a>', url)
    
    download_button.short_description = "Action"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download_application_admin/<int:app_id>/<int:req_id>/', self.admin_site.admin_view(self.download_application_admin), name='download_application_admin'),
        ]
        return custom_urls + urls
    

    def get_list_filter(self, request):
        user = request.user

        if user.groups.filter(name="GM").exists():
            return (GMStatusFilter,) + self.base_filters

        elif user.groups.filter(name="HR").exists():
            return (HRStatusFilter,) + self.base_filters

        elif user.groups.filter(name="DepartmentHead").exists():
            return (DepHeadStatusFilter,) + self.base_filters

        # default for superuser or others
        return ('dep_head_status', 'hr_status', GMStatusFilter) + self.base_filters
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "request_form":
            kwargs["queryset"] = RequestForm.objects.filter(status=1)
        elif db_field.name == "leave_type":
            kwargs["queryset"] = LeaveType.objects.filter(status=1)
        elif db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(status=1)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        auth_user = request.user

        if auth_user.is_superuser:
            return qs

        active_status_value = 1
        dep_ids = DepartmentHead.objects.filter(
            auth_user=auth_user, status=active_status_value
        ).values_list('department_id', flat=True)

        if auth_user.groups.filter(name="HR").exists():
            if dep_ids.exists():
                return (
                    qs.filter(
                    Q(user__department__in=dep_ids) |
                    Q(dep_head_status="Approved") |
                    Q(gm_status__in=["Approved", "Rejected"]),
                    delete_status=False
                    )
                    .exclude(dep_head_status="Rejected", gm_status="Rejected")
                )
            return qs.filter(
                Q(dep_head_status="Approved") |
                Q(gm_status__in=["Approved", "Rejected"]),
                delete_status=False
            )

        if auth_user.groups.filter(name="GM").exists():
            if dep_ids.exists():
                return qs.filter(
                    Q(user__department__in=dep_ids) |
                    Q(hr_status="Approved"),
                    delete_status=False
                )
            return qs.filter(
                hr_status="Approved",
                delete_status=False
            )

        if dep_ids.exists():
            return qs.filter(user__department__in=dep_ids, delete_status=False)

        return qs.filter(user=auth_user, delete_status=False)


    def changelist_view(self, request, extra_context=None):
        """Apply default Pending filter based on role if no filter applied"""
        if not request.GET:  # first load, no filter yet
            user = request.user
            if user.groups.filter(name="HR").exists():
                return redirect(f"{request.path}?{urlencode({'hr_status': 'Pending'})}")
            elif user.groups.filter(name="GM").exists():
                return redirect(f"{request.path}?{urlencode({'gm_status': 'Pending'})}")
            elif DepartmentHead.objects.filter(auth_user=user, status=1).exists():
                return redirect(f"{request.path}?{urlencode({'dep_head_status': 'Pending'})}")

        return super().changelist_view(request, extra_context)
        
    def approve_stage(self, request, queryset):
        stage_field = self._get_stage_field(request) 
        for obj in queryset:
            if obj.request_form_id == 1 or obj.request_form_id == 2 or obj.request_form_id == 3:
                    same_dep = is_same_department(request.user, obj.user.department_id)

                    # Superuser auto-approve all
                    if request.user.is_superuser:
                        obj.dep_head_status = "Approved"
                        obj.hr_status = "Approved"
                        obj.gm_status = "Approved"
                        obj.status = "Approved"
                        self.message_user(request, f"Application {obj.application_id} fully approved by Superuser.")
                        obj.save()
                        continue  # skip further checks

                    if request.user.groups.filter(name__in=['DepartmentHead']).exists():
                        if obj.gm_status in ['Approved', 'Rejected']:
                            self.message_user(
                                    request,
                                    f"Application {obj.application_id} already reviewed by RM. You can’t change the status.",
                                    level=messages.WARNING
                                )
                            continue
                        else: 
                            self.message_user(request, f"Application {obj.application_id} approved at your stage.")
                        setattr(obj, stage_field, 'Approved')

                    elif request.user.groups.filter(name="GM").exists():
                        if same_dep == 1:
                            if obj.dep_head_status == "Pending" and obj.hr_status == "Pending":
                                obj.gm_status = "Approved"
                                obj.dep_head_status = "Approved"
                                obj.status = "Pending"   
                            elif obj.dep_head_status == "Rejected" and obj.hr_status == "Pending":
                                obj.dep_head_status = "Approved"
                                obj.gm_status = "Approved"
                                obj.status = "Pending"
                        else:
                            if obj.dep_head_status == "Approved" and obj.hr_status == "Approved":
                                obj.gm_status = "Approved"
                                obj.status = "Approved"   
                            elif obj.gm_status == "Rejected":
                                obj.gm_status = "Approved"
                                obj.status = "Approved"
                        self.message_user(request, f"Application {obj.application_id} approved at your stage.")
                    elif request.user.groups.filter(name="HR").exists():
                        if obj.gm_status == "Rejected":
                            self.message_user(
                                    request,
                                    f"Application {obj.application_id} already reviewed by RM. You can’t change the status.",
                                    level=messages.WARNING
                                )
                            continue
                        # elif obj.gm_status == "Approved":
                        #     self.message_user(
                        #             request,
                        #             f"Application {obj.application_id} already reviewed by RM. You can’t change the status.",
                        #             level=messages.WARNING
                        #         )
                        #     continue
                        if same_dep == 1:  
                            if  obj.dep_head_status == "Pending" and obj.gm_status == "Pending":
                                obj.hr_status = "Approved"
                                obj.dep_head_status = "Approved"
                                obj.status = "Pending"
                            elif obj.dep_head_status == "Rejected" and obj.gm_status == "Pending":
                                obj.hr_status = "Approved"
                                obj.dep_head_status = "Approved"
                                obj.status = "Pending"
                        else:   
                            if obj.dep_head_status == "Approved" and  obj.gm_status == "Pending":
                                obj.hr_status = "Approved"
                                obj.status = "Pending"
                            elif obj.dep_head_status == "Approved" and  obj.gm_status == "Approved":
                                obj.hr_status = "Approved"
                                obj.status = "Approved"
                            elif obj.dep_head_status == "Rejected" and  obj.gm_status == "Pending":
                                obj.hr_status = "Approved"
                                obj.status = "Pending"
                        self.message_user(request, f"Application {obj.application_id} approved at your stage.")
                    obj.save()
            
            email_for_application(obj,request,action_type="Approved") # Email setup
            
    approve_stage.short_description = "Approve selected applicants"

    def reject_stage(self, request, queryset):
        stage_field = self._get_stage_field(request)
        for obj in queryset:
            if obj.request_form_id == 1 or obj.request_form_id == 2 or obj.request_form_id == 3:
                same_dep = is_same_department(request.user, obj.user.department_id)

                # Superuser auto-rejected all
                if request.user.is_superuser:
                    obj.dep_head_status = "Rejected"
                    obj.hr_status = "Rejected"
                    obj.gm_status = "Rejected"
                    obj.status = "Rejected"
                    self.message_user(request, f"Application {obj.application_id} fully rejected by Superuser.")
                    obj.save()
                    continue  # skip further checks

                if request.user.groups.filter(name__in=['DepartmentHead']).exists():
                    if obj.gm_status in ['Approved', 'Rejected']:
                        self.message_user(
                                request,
                                f"Application {obj.application_id} already reviewed by RM. You can’t change the status.",
                                level=messages.WARNING
                            )
                        continue
                    else:
                        self.message_user(request, f"Application {obj.application_id} rejected at your stage.")
                    setattr(obj, stage_field, 'Rejected')

                elif request.user.groups.filter(name="GM").exists():
                    if same_dep == 1:
                        if obj.dep_head_status == "Approved" and obj.hr_status == "Pending":
                            obj.dep_head_status = "Rejected"
                            obj.gm_status = "Rejected"
                            obj.status = "Rejected"
                        elif obj.dep_head_status == "Pending" and obj.hr_status == "Pending":
                            obj.dep_head_status = "Rejected"
                            obj.gm_status = "Rejected"
                            obj.status = "Rejected"
                        elif obj.dep_head_status == "Approved" and obj.hr_status == "Approved" and obj.status == "Approved":
                            obj.dep_head_status = "Rejected"
                            obj.gm_status = "Rejected"
                            obj.status = "Rejected"
                            obj.hr_status = "Pending"
                    else:
                        if obj.dep_head_status == "Approved" and obj.hr_status == "Approved":
                            obj.gm_status = "Rejected"
                            obj.status = "Rejected"
                    self.message_user(request, f"Application {obj.application_id} rejected at your stage.")    
                elif request.user.groups.filter(name="HR").exists():
                    # HR cannot reject if GM already approved
                    if obj.gm_status == "Approved":
                        self.message_user(
                                request,
                                f"Application {obj.application_id} already reviewed by RM. You can’t change the status.",
                                level=messages.WARNING
                            )
                        continue
                    elif obj.gm_status == "Rejected":
                        self.message_user(
                                request,
                                f"Application {obj.application_id} already reviewed by RM. You can’t change the status.",
                                level=messages.WARNING
                            )
                        continue
                    if same_dep == 1:  
                        if  obj.dep_head_status == "Pending" and obj.gm_status == "Pending":
                            obj.hr_status = "Rejected"
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                        elif obj.dep_head_status == "Approved" and obj.gm_status == "Pending":
                            obj.hr_status = "Rejected"
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                    else:   
                        if obj.dep_head_status == "Approved" and  obj.gm_status == "Pending":
                            obj.hr_status = "Rejected"
                            obj.status = "Rejected"
                        elif obj.dep_head_status == "Approved" and  obj.gm_status == "Approved":
                            obj.hr_status = "Rejected"
                            obj.status = "Rejected"
                    self.message_user(request, f"Application {obj.application_id} rejected at your stage.")
                obj.save()

            email_for_application(obj,request,action_type="Rejected") # Email setup

    reject_stage.short_description = "Reject selected applicants"


    def save_model(self, request, obj, form, change):
        same_dep = is_same_department(request.user, obj.user.department_id)

        if obj.request_form_id == 3:  # Salary Advance
            try:
                month = obj.salary_ad_month
                year = obj.salary_ad_year
                if month and year:
                    year_value = int(year.year)
                    month_value = int(month.number)
                    # Calculate first and last day of the month
                    first_day = datetime.date(year_value, month_value, 1)
                    last_day = datetime.date(year_value, month_value, calendar.monthrange(year_value, month_value)[1])
                    obj.from_date = first_day
                    obj.to_date = last_day
            except Exception as e:
                print(f"Error calculating salary advance period: {e}")
    
        # Rejoining logic (calculate delay_days & total_days_after_rejoin)
        if obj.request_form_id == 2 and obj.rejoin_date:
            try:
                to_dt = obj.to_date
                from_dt = obj.from_date
                rejoin_dt = obj.rejoin_date

                delay_days = 0
                if rejoin_dt > to_dt:
                    delay_days = (rejoin_dt - to_dt).days - 1
                    if delay_days < 0:
                        delay_days = 0

                total_days_after_rejoin = (rejoin_dt - from_dt).days

                obj.delayed_days = delay_days
                obj.total_days_after_rejoin = total_days_after_rejoin

            except Exception as e:
                print(f"Error calculating rejoin days: {e}")

        # Your existing approval logic
        if obj.request_form_id in [1, 2, 3]:  # leave, rejoining, salary advance
            if request.user.groups.filter(name="GM").exists():
                if obj.gm_status == "Approved":
                    if obj.dep_head_status == "Pending":
                        obj.dep_head_status = "Approved"
                    elif obj.dep_head_status == "Approved" and obj.hr_status == "Approved":
                        obj.status = "Approved"
                    elif obj.dep_head_status == "Rejected" and obj.hr_status == "Pending":
                        obj.dep_head_status = "Approved"
                        obj.status = "Pending"
                    email_for_application(obj,request,action_type="Approved") # Email setup
                elif obj.gm_status == "Rejected":
                    if same_dep == 1:
                        if obj.dep_head_status == "Pending":
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                            obj.hr_status = "Pending"
                        elif obj.dep_head_status == "Approved":
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                            obj.hr_status = "Pending"
                        elif obj.dep_head_status == "Approved" and obj.hr_status == "Approved" and obj.status == "Approved":
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                            obj.hr_status = "Pending" 
                    else:
                        if obj.dep_head_status == "Approved" and obj.hr_status == "Approved":
                            obj.status = "Rejected"
                    email_for_application(obj,request,action_type="Rejected") # Email setup
                elif obj.gm_status == "Pending":
                    if same_dep == 1:
                        if obj.dep_head_status == "Approved" and obj.hr_status == "Pending":
                            obj.dep_head_status = "Pending"
                            obj.status = "Pending"
                        elif obj.dep_head_status == "Pending" and obj.hr_status == "Pending":
                            obj.dep_head_status = "Pending"
                            obj.status = "Pending"
                        elif obj.dep_head_status == "Rejected" and obj.hr_status == "Pending":
                            obj.dep_head_status = "Pending"
                            obj.status = "Pending"
                        elif obj.dep_head_status == "Rejected" and obj.hr_status == "Approved":
                            obj.dep_head_status = "Pending"
                            obj.status = "Pending"
                            obj.hr_status = "Pending"
                        elif obj.dep_head_status == "Approved" and obj.hr_status == "Approved" and obj.status == "Approved":
                            obj.dep_head_status = "Pending"
                            obj.status = "Pending"
                            obj.hr_status = "Pending"
                    else:
                        if obj.dep_head_status == "Approved" and obj.hr_status == "Approved":
                            obj.status = "Pending"

            elif request.user.groups.filter(name="HR").exists():
                if obj.hr_status == "Approved":
                    if obj.dep_head_status == "Pending":
                        obj.dep_head_status = "Approved"
                    elif obj.dep_head_status == "Approved" and obj.gm_status == "Approved":
                        obj.status = "Approved"
                    elif obj.dep_head_status == "Approved" and obj.gm_status == "Pending":
                        obj.status = "Pending"
                    elif obj.dep_head_status == "Rejected" and obj.gm_status == "Pending":
                        obj.dep_head_status = "Approved"
                        obj.status = "Pending"
                    email_for_application(obj,request,action_type="Approved") # Email setup
                elif obj.hr_status == "Rejected":
                    if same_dep == 1:
                        if obj.dep_head_status == "Pending":
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                        elif obj.dep_head_status == "Approved" and obj.gm_status == "Pending":
                            obj.dep_head_status = "Rejected"
                            obj.status = "Rejected"
                    else:
                        if obj.dep_head_status == "Approved":
                            obj.status = "Rejected"
                        elif obj.dep_head_status == "Approved" and obj.gm_status == "Pending":
                            obj.status = "Rejected"
                    email_for_application(obj,request,action_type="Rejected") # Email setup
                elif obj.hr_status == "Pending":
                    if same_dep == 1:
                        if obj.dep_head_status == "Approved" and obj.gm_status == "Pending":
                            obj.status = "Pending"
                            obj.dep_head_status = "Pending"             
                        elif obj.dep_head_status == "Rejected" and obj.gm_status == "Pending":
                            obj.dep_head_status = "Pending"
                            obj.status = "Pending"
                    else:
                        if obj.dep_head_status == "Approved" and obj.gm_status == "Pending":
                            obj.status = "Pending"
            
            if request.user.groups.filter(name="DepartmentHead").exists():
                if obj.dep_head_status == "Approved":
                    email_for_application(obj,request,action_type="Approved") # Email setup
                elif obj.dep_head_status == "Rejected":
                    email_for_application(obj,request,action_type="Rejected") # Email setup
        # Save as usual
        super().save_model(request, obj, form, change)

        # --- Update original leave application if this is a Rejoining ---
        if obj.request_form_id == 2 and obj.application_id_rejoin:
            try:
                original_app = Application.objects.get(
                    id=obj.application_id_rejoin,
                    request_form_id=1,  # leave applications only
                    status='Approved',
                    delete_status=False
                )
                original_app.rejoin_status = 1
                original_app.application_id_rejoin = obj.id  # link to this rejoining
                original_app.save(update_fields=['rejoin_status', 'application_id_rejoin'])
            except Application.DoesNotExist:
                pass
    
    def delete_model(self, request, obj):
        """
        Called when an object is permanently deleted from admin.
        Reset original leave application's rejoin_status and link.
        """
        try:
            if obj.request_form_id == 2 and obj.application_id_rejoin:
                # Get the original leave application
                original_app = Application.objects.get(
                    id=obj.application_id_rejoin,
                    request_form_id=1,  # leave applications only
                    status='Approved',
                    delete_status=False
                )
                # Reset the rejoining info
                original_app.rejoin_status = 0
                original_app.application_id_rejoin = None
                original_app.save(update_fields=['rejoin_status', 'application_id_rejoin'])
        except Application.DoesNotExist:
            pass

        # Now delete the rejoining application
        super().delete_model(request, obj)

    def _get_stage_field(self, request):
        if request.user.is_superuser:
            return 'gm_status'
        if request.user.groups.filter(name='DepartmentHead').exists():
            return 'dep_head_status'
        if request.user.groups.filter(name='HR').exists():
            return 'hr_status'
        if request.user.groups.filter(name='GM').exists():
            return 'gm_status'
        return 'dep_head_status'

    def soft_delete_selected(self, request, queryset):
        updated = queryset.update(delete_status=True)
        self.message_user(request, f"{updated} applications marked as deleted.")
    soft_delete_selected.short_description = "Delete selected applicants"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        if not request.user.is_superuser and 'soft_delete_selected' in actions:
            del actions['soft_delete_selected']
        return actions

    def get_list_display(self, request):
        return self.all_fields if request.user.is_superuser else self.limited_fields

    def colored_status(self, obj):
        # Rejection priority: GM > HR > Dep Head
        if obj.gm_status == "Rejected":
            label, status_key = "Rejected by RM", "Rejected"
        elif obj.hr_status == "Rejected":
            label, status_key = "Rejected by HR", "Rejected"
        elif obj.dep_head_status == "Rejected":
            label, status_key = "Rejected by Dep Head", "Rejected"

        # Pending priority: Dep Head → HR → GM
        elif obj.dep_head_status == "Pending":
            label, status_key = "Waiting for Dep Head approval", "Pending"
        elif obj.hr_status == "Pending":
            label, status_key = "Waiting for HR approval", "Pending"
        elif obj.gm_status == "Pending":
            label, status_key = "Waiting for RM approval", "Pending"

        # Final approval (all must be approved)
        else:
            label, status_key = "Approved by RM", "Approved"

        color_map = {
            "Approved": "#5cb85c",  # green
            "Rejected": "#d9534f",  # red
            "Pending": "#4ef0d2",   # teal
        }
        bg_color = color_map.get(status_key, "#ddd")

        return format_html(
            '<span style="background-color:{}; color:black; padding:2px 4px; '
            'border-radius:4px; font-weight:bold; white-space:nowrap;">{}</span>',
            bg_color, label
        )

    colored_status.short_description = 'Status'


    def _colored_stage_status(self, status):
        color_map = {
            'Pending': "#f7fb09d9",
            'Approved': '#5cb85c',
            'Rejected': '#d9534f',
        }
        color = color_map.get(status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: Black; padding: 2px 4px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            status or 'Pending'
        )

    def dep_head_status_display(self, obj):
        return self._colored_stage_status(obj.dep_head_status)
    dep_head_status_display.short_description = "Department Head Status"
    dep_head_status_display.admin_order_field = "dep_head_status"

    def hr_status_display(self, obj):
        return self._colored_stage_status(obj.hr_status)
    hr_status_display.short_description = "HR Status"
    hr_status_display.admin_order_field = "hr_status"

    def gm_status_display(self, obj):
        return self._colored_stage_status(obj.gm_status)
    gm_status_display.short_description = "GM Status"
    gm_status_display.admin_order_field = "gm_status"

    
    # Map of all field labels
    FIELD_LABELS = {
        'user': "Name",
        'request_form': "Request Form",
        'leave_type':"Leave Type",
        'from_date': "From Date",
        'to_date': "To Date",
        'total_days': "Total Days",
        'rejoin_date': "Rejoin Date",
        'application_id_rejoin': "Application For Rejoin",
        'total_days_after_rejoin': "Total Days After Rejoin",
        'delayed_days': "Delayed Days",
        'salary_ad_month': "Salary Advance Month",
        'salary_ad_year': "Salary Advance Year",
        'gm_status': "RM Status",
        'remarks_gm': "Remarks RM",
        'hr_status': "HR Status",
        'remarks_hr': "Remarks HR",
        'dep_head_status': "Department Head Status",
        'remarks_dep_head': "Remarks Dep Head",
        'status': "Status",
        'remarks': "Remarks",
    }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name, label in self.FIELD_LABELS.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label

        # (Show 'leave_type' only if request_form == Leave)
        if obj:
            if hasattr(obj, 'request_form') and obj.request_form_id == 1:  # 1 = Leave form
                # Show only leave types for this request form and active
                if 'leave_type' in form.base_fields:
                    form.base_fields['leave_type'].queryset = LeaveType.objects.filter(
                        request_form_id=obj.request_form_id, status=1
                    )
            else:
                # If not leave form → remove leave_type field
                form.base_fields.pop('leave_type', None)

        return form

    def get_fields(self, request, obj=None):
        if not obj:
            return ['user', 'request_form', 'status', 'remarks']
        if request.user.is_superuser:
            leave_fields = [
                'user', 'request_form','leave_type','from_date', 'to_date', 'total_days',
                'status', 'remarks', 'dep_head_status', 'remarks_dep_head',
                'hr_status', 'remarks_hr', 'gm_status', 'remarks_gm'
            ]
            rejoin_fields = [
                'user', 'request_form', 'rejoin_date','from_date', 'to_date','total_days','delayed_days','total_days_after_rejoin','application_id_rejoin',
                'status','remarks','dep_head_status', 'remarks_dep_head', 'hr_status', 'remarks_hr',
                'gm_status', 'remarks_gm'
            ]
            salary_fields = [
                'user', 'request_form', 'salary_ad_month', 'salary_ad_year',
                'status', 'remarks', 'dep_head_status', 'remarks_dep_head',
                'hr_status', 'remarks_hr', 'gm_status', 'remarks_gm'
            ]
        else:
            leave_fields = [
                'user', 'request_form','leave_type','from_date', 'to_date', 'total_days',
                'status', 'remarks', 'dep_head_status', 'remarks_dep_head',
                'hr_status', 'remarks_hr', 'gm_status', 'remarks_gm'
            ]
            rejoin_fields = [
                'user', 'request_form', 'rejoin_date','from_date', 'to_date',
                'delayed_days', 'status', 'remarks',
                'dep_head_status', 'remarks_dep_head', 'hr_status', 'remarks_hr',
                'gm_status', 'remarks_gm'
            ]
            salary_fields = [
                'user', 'request_form', 'salary_ad_month', 'salary_ad_year',
                'status', 'remarks', 'dep_head_status', 'remarks_dep_head',
                'hr_status', 'remarks_hr', 'gm_status', 'remarks_gm'
            ]

        leave_fields = [f for f in leave_fields if f in self.FIELD_LABELS]
        rejoin_fields = [f for f in rejoin_fields if f in self.FIELD_LABELS]
        salary_fields = [f for f in salary_fields if f in self.FIELD_LABELS]

        if obj.request_form and hasattr(obj.request_form, 'id'):
            if obj.request_form.id == 1:
                return leave_fields
            elif obj.request_form.id == 2:
                return rejoin_fields
            elif obj.request_form.id == 3:
                return salary_fields

        return ['user', 'request_form', 'status', 'remarks']

    def get_readonly_fields(self, request, obj=None):
        """Use FIELD_LABELS keys instead of _meta.fields"""
        all_fields = list(self.FIELD_LABELS.keys())

        if request.user.is_superuser:
            return []

        readonly = []

        if obj:
            if obj.gm_status in ['Approved', 'Rejected']:
                if request.user.groups.filter(name="GM").exists():
                    readonly = [f for f in all_fields if f not in ('gm_status', 'remarks_gm')]
                else:
                    readonly = all_fields
            elif request.user.groups.filter(name='DepartmentHead').exists():
                readonly = [f for f in all_fields if f not in ('dep_head_status', 'remarks_dep_head')]
            elif request.user.groups.filter(name='HR').exists():
                readonly = [f for f in all_fields if f not in ('hr_status', 'remarks_hr')]
            elif request.user.groups.filter(name='GM').exists():
                readonly = [f for f in all_fields if f not in ('gm_status', 'remarks_gm')]
            else:
                readonly = ['dep_head_status', 'remarks_dep_head', 'hr_status', 'remarks_hr',
                            'gm_status', 'remarks_gm']
        else:
            readonly = ['dep_head_status', 'remarks_dep_head', 'hr_status', 'remarks_hr',
                        'gm_status', 'remarks_gm']

        return readonly

    
    def download_application_admin(self,request, app_id, req_id):
        application = get_object_or_404(Application, id=app_id)
        logo_url = request.build_absolute_uri(static('images/awc-logo.jpg'))
        boostrap_url = request.build_absolute_uri(static('css/bootstrap.min.css'))
        application_leave_url = request.build_absolute_uri(static('css/application_leave.css'))
        favicon_url = request.build_absolute_uri(static('images/favicon.ico'))
        # PDFKit config
        config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

        if req_id == 1:
            html = render_to_string("application_leave.html", {
                    "application": application,
                    "today": datetime.date.today(),
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

            pdf = pdfkit.from_string(html, False, options=options, configuration=config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response['Content-Disposition'] = f'attachment; filename="Application_{application.application_id}.pdf"'
            return response
        elif req_id == 2:
            html = render_to_string("application_rejoin.html", {
                    "application": application,
                    "today": datetime.date.today(),
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

            pdf = pdfkit.from_string(html, False, options=options, configuration=config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response['Content-Disposition'] = f'attachment; filename="Application_{application.application_id}.pdf"'
            return response
        elif req_id == 3:
            html = render_to_string("application_salary_ad.html", {
                    "application": application,
                    "today": datetime.date.today(),
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

            pdf = pdfkit.from_string(html, False, options=options, configuration=config)

            response = HttpResponse(pdf, content_type="application/pdf")
            response['Content-Disposition'] = f'attachment; filename="Application_{application.application_id}.pdf"'
            return response



    def user_name(self, obj): return obj.user.name
    def user_batch_number(self, obj): return obj.user.batch_number
    def user_department(self, obj): return obj.user.department.name if obj.user.department else '—'
    def user_nationality(self, obj): return obj.user.nationality.name if obj.user.nationality else '—'
    def user_designation(self, obj): return obj.user.designation.name if obj.user.designation else '—'
    def user_qid(self, obj): return obj.user.qid or '—'

    user_name.short_description = 'Name'
    user_batch_number.short_description = 'Batch #'
    user_department.short_description = 'Department'
    user_nationality.short_description = 'Nationality'
    user_designation.short_description = 'Designation'
    user_qid.short_description = 'QID'

    class Media:
        js = (
            'admin/js/core.js',
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js',
            'admin/js/admin_application_visibility.js',
        )
    