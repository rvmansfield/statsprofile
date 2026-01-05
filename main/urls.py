from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('evaluate/', views.evaluate, name='evaluate'),
    path('results/<int:metric_id>/', views.results, name='results'),
    path('history/', views.metrics_history, name='metrics_history'),
    path('add/', views.add, name='add'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('playerevaluation/', views.playerevaluation, name='playerevaluation'),
    path('<str:username>/', views.profile_by_username, name='profile_by_username'),
]
