from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from django.templatetags.static import static
from django.shortcuts import render
from django.utils.html import format_html
from xhtml2pdf import pisa
import datetime
import csv
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.contrib.admin.sites import site as admin_site
from .forms import ApplicationAdminForm
from django.db.models import Q
from django.contrib.admin.views.main import ChangeList
from .utils import is_same_department
from django.contrib import messages
from .models import (
    User, Ticket, Department, Designation, Item, Inventory,
    InventoryItem, InventoryReport, RequestForm, LeaveType,
    Nationality, DepartmentHead, Application
)

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
        user = users.pop() if len(users) == 1 else None  # ✅ Only one user will be shown

        logo_url = request.build_absolute_uri(static('images/favicon.ico'))
        html = render_to_string('admin/inventory_print.html', {
            'inventories': queryset,
            'user': user,  # ✅ pass user if single user only
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


    # ✅ Inject admin context
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

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    
    all_fields = (
        'application_id',
        'user_batch_number',
        'user_name',
        'user_department',
        'user_designation',
        'user_nationality',
        'user_qid',
        'leave_type',
        'remarks',
        'colored_status',
        'from_date',
        'to_date',
        'total_days',
        'remarks_dep_head',
        'dep_head_status_display',
        'remarks_hr',
        'hr_status_display',
        'remarks_gm',
        'gm_status_display',
        'entry_date',
    )

    limited_fields = (
        'application_id',
        'user_batch_number',
        'user_name',
        'user_department',
        'leave_type',
        'remarks',
        'from_date',
        'to_date',
        'total_days',
        'colored_status',
    )

    list_per_page = 20
    base_filters  = (
        'leave_type',
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
            if obj.request_form_id == 1:
                    same_dep = is_same_department(request.user, obj.user.department_id)

                    # ✅ Superuser auto-approve all
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

    approve_stage.short_description = "Approve selected applicants"

    def reject_stage(self, request, queryset):
        stage_field = self._get_stage_field(request)
        for obj in queryset:
            if obj.request_form_id == 1:
                same_dep = is_same_department(request.user, obj.user.department_id)

                # ✅ Superuser auto-rejected all
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
                    # 🚫 HR cannot reject if GM already approved
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

    reject_stage.short_description = "Reject selected applicants"

    def save_model(self, request, obj, form, change):

        same_dep = is_same_department(request.user, obj.user.department_id)

        if obj.request_form_id == 1:   # example: only apply logic for Leave Application

            if request.user.groups.filter(name="GM").exists():
                if obj.gm_status == "Approved":
                    if obj.dep_head_status == "Pending":
                        obj.dep_head_status = "Approved"
                    elif obj.dep_head_status == "Approved" and obj.hr_status == "Approved":
                        obj.status = "Approved"
                    elif obj.dep_head_status == "Rejected" and obj.hr_status == "Pending":
                        obj.dep_head_status = "Approved"
                        obj.status = "Pending"
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
            super().save_model(request, obj, form, change)

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
        # ✅ Rejection priority: GM > HR > Dep Head
        if obj.gm_status == "Rejected":
            label, status_key = "Rejected by RM", "Rejected"
        elif obj.hr_status == "Rejected":
            label, status_key = "Rejected by HR", "Rejected"
        elif obj.dep_head_status == "Rejected":
            label, status_key = "Rejected by Dep Head", "Rejected"

        # ✅ Pending priority: Dep Head → HR → GM
        elif obj.dep_head_status == "Pending":
            label, status_key = "Waiting for Dep Head approval", "Pending"
        elif obj.hr_status == "Pending":
            label, status_key = "Waiting for HR approval", "Pending"
        elif obj.gm_status == "Pending":
            label, status_key = "Waiting for RM approval", "Pending"

        # ✅ Final approval (all must be approved)
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

    def get_readonly_fields(self, request, obj=None):

        if request.user.is_superuser:
            return []
        
        if not obj:
            return super().get_readonly_fields(request, obj)

        if obj.gm_status in ['Approved', 'Rejected']:
            all_fields = [f.name for f in self.model._meta.fields]
            if request.user.groups.filter(name="GM").exists():
                editable_fields = ['gm_status', 'remarks_gm']
                return [f for f in all_fields if f not in editable_fields]
            else:
                return all_fields

        if request.user.groups.filter(name='DepartmentHead').exists():
            return [f.name for f in self.model._meta.fields
                    if f.name not in ('remarks_dep_head', 'dep_head_status')]

        if request.user.groups.filter(name='HR').exists():
            return [f.name for f in self.model._meta.fields
                    if f.name not in ('remarks_hr', 'hr_status')]

        if request.user.groups.filter(name='GM').exists():
            return [f.name for f in self.model._meta.fields
                    if f.name not in ('remarks_gm', 'gm_status')]

        readonly = list(super().get_readonly_fields(request, obj))
        readonly.extend(['dep_head_status', 'remarks_dep_head'])
        return readonly

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
            'js/calculate_days.js',
        )