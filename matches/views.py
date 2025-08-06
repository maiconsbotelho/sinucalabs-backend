from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, Max, Min
from django.utils import timezone
from django.db import models
from .models import Match, MatchPlayer, Move
from .serializers import (
    MatchSerializer,
    MatchListSerializer,
    MoveSerializer,
    CreateMoveSerializer,
    MatchStatsSerializer
)
from core.achievement_engine import achievement_engine


class MatchListCreateView(generics.ListCreateAPIView):
    """Lista e cria partidas"""
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']
    search_fields = ['created_by__display_name']
    ordering = ['-started_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MatchSerializer
        return MatchListSerializer
    
    def get_queryset(self):
        user = self.request.user
        # Retorna partidas onde o usuário é criador ou participante
        return Match.objects.filter(
            Q(created_by=user) | Q(match_players__user=user)
        ).distinct()


class MatchDetailView(generics.RetrieveUpdateAPIView):
    """Detalhes e atualização de partida"""
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            Q(created_by=user) | Q(match_players__user=user)
        ).distinct()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def finish_match(request, match_id):
    """Finaliza uma partida e avalia conquistas"""
    match = get_object_or_404(Match, id=match_id)
    user = request.user
    
    # Verifica se o usuário pode finalizar a partida
    if match.created_by != user and not match.match_players.filter(user=user).exists():
        return Response(
            {'error': 'Você não tem permissão para finalizar esta partida'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if match.status != 'em_andamento':
        return Response(
            {'error': 'Esta partida já foi finalizada'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Finaliza a partida
    match.status = 'finalizada'
    match.ended_at = timezone.now()
    
    # Calcula duração
    if match.started_at and match.ended_at:
        duration = match.ended_at - match.started_at
        match.duration_minutes = int(duration.total_seconds() / 60)
    
    match.save()
    
    # Avalia conquistas
    unlocked_achievements = achievement_engine.evaluate_match_achievements(match)
    
    # Prepara resposta com conquistas desbloqueadas
    achievements_data = []
    for achievement_data in unlocked_achievements:
        from achievements.serializers import UserAchievementSerializer
        achievements_data.append({
            'user': achievement_data['user'].display_name,
            'achievement': {
                'name': achievement_data['achievement'].name,
                'description': achievement_data['achievement'].description,
                'category': achievement_data['achievement'].category,
                'points': achievement_data['achievement'].points
            }
        })
    
    return Response({
        'message': 'Partida finalizada com sucesso!',
        'match': MatchSerializer(match).data,
        'unlocked_achievements': achievements_data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_move(request, match_id):
    """Adiciona uma jogada à partida"""
    match = get_object_or_404(Match, id=match_id)
    user = request.user
    
    # Verifica se a partida está em andamento
    if match.status != 'em_andamento':
        return Response(
            {'error': 'Não é possível adicionar jogadas a uma partida finalizada'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verifica se o usuário é participante da partida
    try:
        player = match.match_players.get(user=user)
    except MatchPlayer.DoesNotExist:
        return Response(
            {'error': 'Você não é participante desta partida'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = CreateMoveSerializer(
        data=request.data,
        context={'match': match, 'player': player}
    )
    
    if serializer.is_valid():
        move = serializer.save()
        
        # Avalia conquistas após cada jogada
        unlocked_achievements = achievement_engine.evaluate_user_achievements(user, match)
        
        response_data = {
            'move': MoveSerializer(move).data,
            'player_points': player.points
        }
        
        if unlocked_achievements:
            from achievements.serializers import UserAchievementSerializer
            response_data['unlocked_achievements'] = [
                {
                    'achievement': {
                        'name': ach['achievement'].name,
                        'description': ach['achievement'].description,
                        'category': ach['achievement'].category
                    }
                } for ach in unlocked_achievements
            ]
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def match_stats(request):
    """Estatísticas de partidas do usuário"""
    user = request.user
    
    # Partidas do usuário
    user_matches = MatchPlayer.objects.filter(user=user)
    total_matches = user_matches.count()
    
    if total_matches == 0:
        return Response({
            'total_matches': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'average_points': 0,
            'total_moves': 0,
            'favorite_move_type': None,
            'longest_match_duration': 0,
            'shortest_match_duration': 0
        })
    
    # Vitórias e derrotas
    wins = user_matches.filter(is_winner=True).count()
    losses = total_matches - wins
    win_rate = (wins / total_matches) * 100
    
    # Pontos médios
    average_points = user_matches.aggregate(avg_points=Avg('points'))['avg_points'] or 0
    
    # Total de jogadas
    total_moves = Move.objects.filter(player__user=user).count()
    
    # Tipo de jogada favorito
    favorite_move = Move.objects.filter(
        player__user=user
    ).values('move_type').annotate(
        count=Count('move_type')
    ).order_by('-count').first()
    
    favorite_move_type = favorite_move['move_type'] if favorite_move else None
    
    # Duração das partidas
    finished_matches = Match.objects.filter(
        match_players__user=user,
        status='finalizada',
        duration_minutes__isnull=False
    )
    
    longest_duration = finished_matches.aggregate(
        max_duration=Max('duration_minutes')
    )['max_duration'] or 0
    
    shortest_duration = finished_matches.aggregate(
        min_duration=Min('duration_minutes')
    )['min_duration'] or 0
    
    data = {
        'total_matches': total_matches,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 2),
        'average_points': round(average_points, 2),
        'total_moves': total_moves,
        'favorite_move_type': favorite_move_type,
        'longest_match_duration': longest_duration,
        'shortest_match_duration': shortest_duration
    }
    
    return Response(data)


class MatchHistoryView(generics.ListAPIView):
    """Histórico de partidas do usuário"""
    serializer_class = MatchListSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-started_at']
    
    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            match_players__user=user
        ).distinct()