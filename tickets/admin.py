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
from django.contrib.admin.sites import site as admin_site

from .models import User, Ticket, Department, Item, Inventory, InventoryItem,InventoryReport

admin.site.site_header = "IT Ticketing Admin"
admin.site.site_title = "IT Ticketing Admin Portal"
admin.site.index_title = "Welcome to IT Ticketing System"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_number', 'department', 'mobile_number','status', 'password')
    search_fields = ('name', 'batch_number')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_batch_number', 'user_department', 'item', 'status', 'request_date')
    list_filter = ('status', 'item', 'user__department')
    search_fields = ('user__name', 'user__batch_number', 'item__name', 'description')

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
                f'Department: {selected_user_obj.department.name if selected_user_obj.department else ""}'
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
