from django.db import models
from django.contrib.auth.hashers import make_password
from datetime import date
from django.utils.html import format_html
import uuid
from django.contrib.auth.models import User as AuthUser

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
    batch_number = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    nationality = models.ForeignKey(Nationality, on_delete=models.SET_NULL, null=True, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    qid = models.CharField(max_length=50, unique=True)  
    qid_expiry_date = models.DateField(default=today)  
    date_of_joining = models.DateField(default=today)
    address = models.TextField(blank=True)
    passport_number = models.CharField(max_length=50, unique=True)
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
    inventory_id = models.CharField(max_length=20, unique=True, blank=False, null=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.inventory_id:
            # Sequential ID: INV-0001, INV-0002
            last_item = InventoryItem.objects.order_by('-id').first()
            if last_item and last_item.inventory_id:
                last_number = int(last_item.inventory_id.split('-')[-1])
            else:
                last_number = 0
            self.inventory_id = f"INVE-{last_number + 1:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.inventory_id}  - {self.name}"
    
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
    auth_user = models.ForeignKey(AuthUser, on_delete=models.CASCADE,null=False)  # new field
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.auth_user.username} - {self.department.name}"

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
    application_id = models.CharField(max_length=20, unique=True, blank=False,null=True,editable=False)
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

    def save(self, *args, **kwargs):
        if not self.application_id:
            # Generate a random 8-character unique ID
            self.application_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        # 🔑 Final approval logic
        if (
            self.dep_head_status == "Approved"
            and self.hr_status == "Approved"
            and self.gm_status == "Approved"
        ):
            self.status = "Approved"
        elif (
            self.dep_head_status == "Rejected"
            or self.hr_status == "Rejected"
            or self.gm_status == "Rejected"
        ):
            self.status = "Rejected"
        else:
            self.status = "Pending"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_id} - {self.user.name} - {self.leave_type.name}"

