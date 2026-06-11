from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_report),
    path('<int:pk>/', views.manage_reports),
    path('manage/', views.manage_reports),  # GET /api/reports/manage/ (관리자 전체 조회 및 유저 조회)
    path('manage/<int:pk>/', views.manage_reports),
]
