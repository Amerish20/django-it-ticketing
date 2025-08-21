from django.db import migrations

def migrate_user_to_auth_user(apps, schema_editor):
    DepartmentHead = apps.get_model('tickets', 'DepartmentHead')
    OldUser = apps.get_model('tickets', 'User')
    AuthUser = apps.get_model('auth', 'User')

    for dh in DepartmentHead.objects.all():
        if dh.user_id:
            try:
                # Example: assuming old User.name = auth_user.username
                auth_user = AuthUser.objects.get(username=dh.user.name)
                dh.auth_user = auth_user
                dh.save()
            except AuthUser.DoesNotExist:
                # log missing matches
                print(f"⚠️ No auth_user found for old user {dh.user.name}")

def reverse_migration(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0024_departmenthead_auth_user_alter_departmenthead_user'),
    ]

    operations = [
        migrations.RunPython(migrate_user_to_auth_user, reverse_migration),
    ]
