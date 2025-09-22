from .models import DepartmentHead

def is_same_department(user, employee_department_id):
    """
    Check if the logged-in user is DepartmentHead of the employee's department.
    Returns 1 if same department, else 0.
    """
    user_departments = DepartmentHead.objects.filter(
        auth_user=user, status=1
    ).values_list("department_id", flat=True)

    return 1 if employee_department_id in user_departments else 0
