from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    # Listar e criar partidas
    path('', views.MatchListCreateView.as_view(), name='match_list_create'),
    
    # Detalhes de uma partida específica
    path('<uuid:pk>/', views.MatchDetailView.as_view(), name='match_detail'),
    
    # Finalizar partida
    path('<uuid:match_id>/finish/', views.finish_match, name='finish_match'),
    
    # Adicionar jogada
    path('<uuid:match_id>/moves/', views.add_move, name='add_move'),
    
    # Estatísticas de partidas do usuário
    path('stats/', views.match_stats, name='match_stats'),
    
    # Histórico de partidas
    path('history/', views.MatchHistoryView.as_view(), name='match_history'),
]