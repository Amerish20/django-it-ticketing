from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('change_password/', views.change_password, name='change_password'),
    path('edit-application/<int:application_id>/', views.edit_application, name='edit_application'),
    path('delete-application/<int:application_id>/', views.delete_application, name='delete_application'),
    path('submit-application/', views.submit_application, name='submit_application'),
    path('logout/', views.logout_view, name='logout'),
    path('download-application/<int:app_id>/<int:req_id>/', views.download_application, name='download_application'),
    path('application-print/<int:app_id>/<int:req_id>/', views.print_application, name='print_application'),
    path("get-leave-types/<int:req_id>/", views.get_leave_types, name="get_leave_types"),
    path('email-test/', views.email_test, name='email_test'),

]
