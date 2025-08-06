from django.urls import path
from . import views

app_name = 'championships'

urlpatterns = [
    # Listar e criar campeonatos
    path('', views.ChampionshipListCreateView.as_view(), name='championship_list_create'),
    
    # Detalhes de um campeonato específico
    path('<uuid:pk>/', views.ChampionshipDetailView.as_view(), name='championship_detail'),
    
    # Participar de um campeonato
    path('join/', views.join_championship, name='join_championship'),
    
    # Sair de um campeonato
    path('<uuid:championship_id>/leave/', views.leave_championship, name='leave_championship'),
    
    # Iniciar campeonato
    path('<uuid:championship_id>/start/', views.start_championship, name='start_championship'),
    
    # Finalizar campeonato
    path('<uuid:championship_id>/finish/', views.finish_championship, name='finish_championship'),
    
    # Criar partida de campeonato
    path('matches/create/', views.create_championship_match, name='create_championship_match'),
    
    # Estatísticas de campeonatos do usuário
    path('stats/', views.championship_stats, name='championship_stats'),
    
    # Meus campeonatos
    path('my/', views.MyChampionshipsView.as_view(), name='my_championships'),
    
    # Ranking de um campeonato
    path('<uuid:championship_id>/leaderboard/', views.championship_leaderboard, name='championship_leaderboard'),
]