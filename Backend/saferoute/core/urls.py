from django.urls import path
from . import views

urlpatterns = [
    # Route risk score endpoints
    path('routes/', views.RouteRiskScoreView.as_view(), name='route-list'),
    path('routes/<str:route_id>/', views.RouteRiskScoreView.as_view(), name='route-detail'),
    path('compare-routes/', views.RouteRiskComparisonView.as_view(), name='compare-routes'),
]