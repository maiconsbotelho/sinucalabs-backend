from django.urls import path
from . import views

app_name = 'achievements'

urlpatterns = [
    path('', views.AchievementListView.as_view(), name='achievement_list'),
    path('my/', views.UserAchievementListView.as_view(), name='user_achievement_list'),
    path('my/<uuid:pk>/', views.UserAchievementDetailView.as_view(), name='user_achievement_detail'),
    path('stats/', views.achievement_stats, name='achievement_stats'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('<uuid:achievement_id>/progress/', views.achievement_progress, name='achievement_progress'),
]