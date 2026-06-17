from django.urls import path
from . import views

urlpatterns = [
    # 프론트엔드가 접근할 주소: /api/robot_tasks/conveyor/
    path('conveyor/', views.operate_conveyor, name='operate-conveyor'),
]