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
from .models import (
    User, Ticket, Department, Designation, Item, Inventory,
    InventoryItem, InventoryReport, RequestForm, LeaveType,
    Nationality, DepartmentHead, Application
)

admin.site.index_title = "Welcome to Al Wataniya Concrete Admin Portal"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)
    list_per_page = 20


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)
    list_per_page = 20


@admin.register(Nationality)
class NationalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'batch_number',
        'department',
        'designation',
        'mobile_number',
        'qid',
        'qid_expiry_date',
        'nationality',
        'passport_number',
        'passport_expiry_date',
        'marital_status',
        'status',
        'password',
    )
    list_filter = (
        'department', 'status','nationality','designation'
    )
    search_fields = ('name', 'batch_number')
    list_per_page = 20
    

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    
    all_fields = (
        'user_batch_number',
        'user_name',
        'user_department',
        'user_designation',
        'user_nationality',
        'user_qid',
        'leave_type',
        'colored_status',
        'from_date',
        'to_date',
        'total_days',
        'remarks_dep_head',
        'dep_head_status_display',  # use colored display here
        'remarks_hr',
        'hr_status_display',        # use colored display here
        'remarks_gm',
        'gm_status_display',        # use colored display here
        'entry_date',
    )

    limited_fields = (
        'user_batch_number',
        'user_name',
        'user_department',
        'leave_type',
        'from_date',
        'to_date',
        'total_days',
        'colored_status',
    )

    list_per_page = 20
    list_filter = (
        'dep_head_status', 'hr_status', 'gm_status',
        'leave_type', 'from_date', 'to_date',
        'user__department', 'user__nationality'
    )
    search_fields = (
        'user__name', 'user__batch_number',
        'leave_type__name',
        'dep_head_status', 'hr_status', 'gm_status'
    )

    actions = [
        'approve_stage', 'reject_stage', 'soft_delete_selected'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        auth_user = request.user

        try:
            custom_user = User.objects.get(name=auth_user.username)
        except User.DoesNotExist:
            return qs

        if auth_user.is_superuser:
            return qs

        active_status_value = 1
        dep_ids = DepartmentHead.objects.filter(
            user=custom_user, status=active_status_value
        ).values_list('department', flat=True)

        if dep_ids.exists():
            return qs.filter(user__department__in=dep_ids, delete_status=False)

        return qs.filter(user=custom_user, delete_status=False)

    def approve_stage(self, request, queryset):
        stage_field = self._get_stage_field(request)
        updated = queryset.update(**{stage_field: 'Approved'})
        self.message_user(request, f"{updated} applications approved at your stage.")

    approve_stage.short_description = "Approve selected applicants"

    def reject_stage(self, request, queryset):
        stage_field = self._get_stage_field(request)
        updated = queryset.update(**{stage_field: 'Rejected'})
        self.message_user(request, f"{updated} applications rejected at your stage.")

    reject_stage.short_description = "Reject selected applicants"

    def _get_stage_field(self, request):
        if request.user.is_superuser:
            return 'gm_status'
        if request.user.groups.filter(name='DepartmentHead').exists():
            return 'dep_head_status'
        if request.user.groups.filter(name='HR').exists():
            return 'hr_status'
        if request.user.groups.filter(name='GM').exists():
            return 'gm_status'
        return 'dep_head_status'  # fallback

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
        status_text = obj.final_status()
        color_map = {
            'Pending': "#f7fb09d9",
            'Approved': '#5cb85c',
            'Rejected by GM': '#d9534f',
            'Rejected by HR': '#d9534f',
            'Rejected by Department Head': '#d9534f',
        }
        bg_color = color_map.get(status_text, "")
        return format_html(
            '<span style="background-color: {}; color: Black; padding: 2px 4px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            bg_color,
            status_text,
        )
    colored_status.short_description = 'Status'

    # Colored status display helpers for individual stages
    def _colored_stage_status(self, status):
        color_map = {
            'Pending': "#f7fb09d9",   # yellow/orange
            'Approved': '#5cb85c',  # green
            'Rejected': '#d9534f',  # red
        }
        color = color_map.get(status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: Black; padding: 2px 4px; border-radius: 4px; font-weight: bold;">{}</span>',
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

    # User info methods
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
        css = {
            'all': ('css/admin/custom_admin.css',)
        }

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_batch_number', 'user_department', 'item', 'status', 'request_date')
    list_filter = ('status', 'item', 'user__department')
    search_fields = ('user__name', 'user__batch_number', 'item__name', 'description')
    list_per_page = 20

    def user_name(self, obj): return obj.user.name
    def user_batch_number(self, obj): return obj.user.batch_number
    def user_department(self, obj): return obj.user.department.name if obj.user.department else '—'

    user_name.short_description = 'User'
    user_batch_number.short_description = 'Batch Number'
    user_department.short_description = 'Department'


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'serial_number', 'asset_code', 'buy_date', 'status')
    search_fields = ('name', 'serial_number', 'asset_code')
    list_per_page = 20


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
    actions = ['generate_combined_pdf']

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
        logo_url = request.build_absolute_uri(static('images/favicon.ico'))

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
    list_display = ('name', 'status')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name','request_form', 'status')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(DepartmentHead)
class DepartmentHeadAdmin(admin.ModelAdmin):
    list_display = ('department','user', 'status')
    list_filter = ('status', 'department')
    search_fields = ('user__name', 'department__name')
    list_per_page = 20

