"""
URL configuration for myapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from FRONTEND import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.page_home, name='Home'),
    path('checkout', views.page_checkout, name='Checkout'),
    path('checkout/invoice', views.page_digital_checkin, name='Checkin digital'),
    path('checkout/invoice/error/<id>', views.page_digital_checkin_error, name='Checkin digital error'),
    path('checkout/cash', views.page_cash_checkin, name='Checkin cash'),
    path('login', views.page_login, name='Login'),
    path('logout', views.func_logout, name='Logout'),
    path('delete/<id>', views.delete_ticket, name='Delete'),
    path('log/<logfile>', views.log_view, name='Log'),
]
