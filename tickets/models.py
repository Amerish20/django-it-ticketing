from django.db import models
from django.contrib.auth.hashers import make_password
from datetime import date
from django.utils.html import format_html

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected'),
    ('Completed', 'Completed'),
]

INVENTORY_STATUS_CHOICES = [
    (1, 'Issued'),
    (2, 'Returned'),
    (3, 'Lost'),
]


ACTIVE_STATUS = [
    (0, 'Inactive'),
    (1, 'Active'),
]

MARITAL_STATUS_CHOICES = [
    ('Single', 'Single'),
    ('Married', 'Married'),
]

def today():
    return date.today()

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.name}"

class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.name} ({'Active' if self.status else 'Inactive'})"

class Designation(models.Model):
    name = models.CharField(max_length=100)
    status = models.IntegerField(choices=((0, 'Inactive'), (1, 'Active')), default=1)

    def __str__(self):
        return self.name
    
class Nationality(models.Model):
    name = models.CharField(max_length=100)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return self.name

class User(models.Model):
    name = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    nationality = models.ForeignKey(Nationality, on_delete=models.SET_NULL, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    qid = models.CharField(max_length=50)  
    qid_expiry_date = models.DateField(default=today)  
    date_of_joining = models.DateField(default=today)
    address = models.TextField(blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry_date = models.DateField(null=True, blank=True)
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        null=True, blank=True,default=None
    )
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)
    password = models.CharField(max_length=128)

    def __str__(self):
        dept_name = self.department.name if self.department else "No Dept"
        return f"{self.name} - ({self.batch_number}) ({dept_name})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.user.name} - {self.item.name} ({self.status})"


class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, unique=True)
    asset_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    buy_date = models.DateField(null=True, blank=True)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.name}"
    
class Inventory(models.Model):
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)

    issue_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    inventory_status = models.IntegerField(choices=INVENTORY_STATUS_CHOICES, default=1)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)
    remarks = models.TextField(blank=True)
    entry_date = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.inventory_item} assigned to {self.user.name if self.user else 'N/A'}"
    
class InventoryReport(models.Model):
    class Meta:
        managed = False
        verbose_name = "Inventory Report"
        verbose_name_plural = "Inventory Report"    


class RequestForm(models.Model):
    name = models.CharField(max_length=100)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return self.name  

class LeaveType(models.Model):
    request_form = models.ForeignKey(RequestForm, on_delete=models.CASCADE, related_name='leave_types')
    name = models.CharField(max_length=100)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return self.name
    
class DepartmentHead(models.Model):
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.user.name} - {self.department.name}"

class ApplicationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(delete_status=False)
    
class Application(models.Model):
    class Meta:
        verbose_name_plural = "Applications"
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    request_form = models.ForeignKey('RequestForm', on_delete=models.CASCADE)
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True)
    remarks_dep_head = models.TextField(blank=True)
    remarks_hr = models.TextField(blank=True)
    remarks_gm = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    delete_status = models.BooleanField(default=0)  # 0 = not deleted, 1 = deleted
    entry_date = models.DateTimeField(auto_now_add=True)

    # Status for each stage
    dep_head_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    hr_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    gm_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    delete_status = models.BooleanField(default=0)  # 0 = not deleted, 1 = deleted
    entry_date = models.DateTimeField(auto_now_add=True)

    objects = ApplicationManager()
    all_objects = models.Manager()  # To access all including deleted

    def __str__(self):
        return f"{self.user.name} - {self.leave_type.name}"

    def final_status(self):
        color_map = {
            "Approved": "#5cb85c",  # green
            "Rejected": "#d9534f",  # red
            "Pending": "#4ef0d2",
        }

        # Approval flow logic
        if self.gm_status == "Approved":
            label = "Approved"
            status_key = "Approved"
        elif self.gm_status == "Rejected":
            label = "Rejected by GM"
            status_key = "Rejected"
        elif self.hr_status == "Rejected":
            label = "Rejected by HR"
            status_key = "Rejected"
        elif self.dep_head_status == "Rejected":
            label = "Rejected by Dep Head"
            status_key = "Rejected"
        elif self.dep_head_status == "Pending":
            label = "Waiting for Dep Head approval"
            status_key = "Pending"
        elif self.hr_status == "Pending":
            label = "Waiting for HR approval"
            status_key = "Pending"
        elif self.gm_status == "Pending":
            label = "Waiting for GM approval"
            status_key = "Pending"
        else:
            label = "Pending"
            status_key = "Pending"

        text_color = color_map.get(status_key, "")

        return format_html(
            '<span style="background-color:{};color:black;padding:2px 4px;'
            'border-radius:4px;font-weight:bold;white-space:nowrap;">{}</span>',
            text_color,
            label
        )

        final_status.short_description = "Final Status"
        final_status.admin_order_field = "gm_status"
