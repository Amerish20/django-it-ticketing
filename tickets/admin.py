from django.contrib import admin
from .models import User, Ticket, Department, Item


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
    list_display = ('name', 'batch_number', 'department', 'status','password')
    search_fields = ('name', 'batch_number')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_batch_number', 'user_department', 'item', 'status', 'request_date')
    list_filter = ('status', 'item', 'user__department')
    search_fields = ('user__name', 'user__batch_number', 'item__name', 'description')

    def user_name(self, obj):
        return obj.user.name
    user_name.short_description = 'User'

    def user_batch_number(self, obj):
        return obj.user.batch_number
    user_batch_number.short_description = 'Batch Number'

    def user_department(self, obj):
        return obj.user.department.name if obj.user.department else '—'
    user_department.short_description = 'Department'


