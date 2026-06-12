from django.urls import path
from . import views

urlpatterns = [
    # POST /api/pickup/verify-code/
    path('verify-code/', views.verify_code),
    
    # POST /api/pickup/confirm/
    path('confirm/', views.confirm_pickup),
]