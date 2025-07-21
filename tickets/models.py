from django.db import models
from django.contrib.auth.hashers import make_password

STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected'),
    ('Completed', 'Completed'),
]

ACTIVE_STATUS = [
    (0, 'Inactive'),
    (1, 'Active'),
]

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.name} ({'Active' if self.status else 'Inactive'})"

class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)

    def __str__(self):
        return f"{self.name} ({'Active' if self.status else 'Inactive'})"

class User(models.Model):
    name = models.CharField(max_length=100)
    batch_number = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    status = models.IntegerField(choices=ACTIVE_STATUS, default=1)  
    password = models.CharField(max_length=128)  # Store hashed password

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
