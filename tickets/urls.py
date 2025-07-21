from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('logout/', views.logout_view, name='logout'),
]
