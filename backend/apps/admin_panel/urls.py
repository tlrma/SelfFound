from django.urls import path
from . import views

urlpatterns = [
    path('', views.alerts, name='admin-alerts'),
    path('<int:pk>/dismiss/', views.dismiss_alert, name='admin-alert-dismiss'),
]
