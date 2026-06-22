from django.urls import path

from . import views

urlpatterns = [
    path('review/<int:report_id>/', views.review_candidates),
    path('review/<int:match_id>/decide/', views.decide_review_candidate),
]
