from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Championship, ChampionshipMatch, ChampionshipParticipant
from .serializers import (
    ChampionshipSerializer,
    ChampionshipListSerializer,
    JoinChampionshipSerializer,
    CreateChampionshipMatchSerializer,
    ChampionshipStatsSerializer
)
from matches.models import Match, MatchPlayer
from matches.serializers import MatchSerializer

User = get_user_model()


class ChampionshipListCreateView(generics.ListCreateAPIView):
    """Lista e cria campeonatos"""
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_finished']
    search_fields = ['name', 'description', 'created_by__display_name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChampionshipSerializer
        return ChampionshipListSerializer
    
    def get_queryset(self):
        # Retorna todos os campeonatos públicos
        return Championship.objects.all()


class ChampionshipDetailView(generics.RetrieveUpdateAPIView):
    """Detalhes e atualização de campeonato"""
    serializer_class = ChampionshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Championship.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # Apenas o criador pode editar
        if self.request.method in ['PUT', 'PATCH']:
            if obj.created_by != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Apenas o criador pode editar este campeonato.")
        return obj


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def join_championship(request):
    """Participar de um campeonato"""
    serializer = JoinChampionshipSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        championship_id = serializer.validated_data['championship_id']
        championship = get_object_or_404(Championship, id=championship_id)
        
        # Cria participação
        participant = ChampionshipParticipant.objects.create(
            championship=championship,
            user=request.user
        )
        
        return Response({
            'message': 'Você se inscreveu no campeonato com sucesso!',
            'championship': ChampionshipListSerializer(championship).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_championship(request, championship_id):
    """Sair de um campeonato"""
    championship = get_object_or_404(Championship, id=championship_id)
    user = request.user
    
    if championship.is_finished:
        return Response(
            {'error': 'Não é possível sair de um campeonato finalizado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if championship.started_at:
        return Response(
            {'error': 'Não é possível sair de um campeonato já iniciado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        participant = championship.participants.get(user=user)
        participant.delete()
        
        return Response({
            'message': 'Você saiu do campeonato com sucesso!'
        })
    except ChampionshipParticipant.DoesNotExist:
        return Response(
            {'error': 'Você não está participando deste campeonato'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_championship(request, championship_id):
    """Iniciar um campeonato"""
    championship = get_object_or_404(Championship, id=championship_id)
    user = request.user
    
    if championship.created_by != user:
        return Response(
            {'error': 'Apenas o criador pode iniciar o campeonato'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if championship.started_at:
        return Response(
            {'error': 'Este campeonato já foi iniciado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if championship.is_finished:
        return Response(
            {'error': 'Este campeonato já foi finalizado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verifica se há participantes suficientes
    participant_count = championship.participants.count()
    if participant_count < 2:
        return Response(
            {'error': 'É necessário pelo menos 2 participantes para iniciar o campeonato'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Inicia o campeonato
    championship.started_at = timezone.now()
    championship.save()
    
    return Response({
        'message': 'Campeonato iniciado com sucesso!',
        'championship': ChampionshipSerializer(championship).data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def finish_championship(request, championship_id):
    """Finalizar um campeonato"""
    championship = get_object_or_404(Championship, id=championship_id)
    user = request.user
    
    if championship.created_by != user:
        return Response(
            {'error': 'Apenas o criador pode finalizar o campeonato'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if championship.is_finished:
        return Response(
            {'error': 'Este campeonato já foi finalizado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not championship.started_at:
        return Response(
            {'error': 'Este campeonato ainda não foi iniciado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Finaliza o campeonato
    championship.is_finished = True
    championship.ended_at = timezone.now()
    championship.save()
    
    return Response({
        'message': 'Campeonato finalizado com sucesso!',
        'championship': ChampionshipSerializer(championship).data,
        'champion': ChampionshipListSerializer(championship).data.get('champion')
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_championship_match(request):
    """Criar partida de campeonato"""
    serializer = CreateChampionshipMatchSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        championship_id = serializer.validated_data['championship_id']
        participant_ids = serializer.validated_data['participant_ids']
        round_number = serializer.validated_data['round_number']
        
        championship = get_object_or_404(Championship, id=championship_id)
        
        # Cria a partida
        match = Match.objects.create(
            created_by=request.user,
            status='em_andamento'
        )
        
        # Adiciona jogadores à partida
        for i, participant_id in enumerate(participant_ids):
            user = get_object_or_404(User, id=participant_id)
            MatchPlayer.objects.create(
                match=match,
                user=user,
                team=i + 1,
                position=i + 1
            )
        
        # Associa a partida ao campeonato
        championship_match = ChampionshipMatch.objects.create(
            championship=championship,
            match=match,
            round_number=round_number
        )
        
        return Response({
            'message': 'Partida de campeonato criada com sucesso!',
            'match': MatchSerializer(match).data,
            'championship_match_id': championship_match.id
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def championship_stats(request):
    """Estatísticas de campeonatos do usuário"""
    user = request.user
    
    # Campeonatos participados
    participated_championships = Championship.objects.filter(
        participants__user=user
    ).distinct()
    
    total_championships = participated_championships.count()
    
    if total_championships == 0:
        return Response({
            'total_championships': 0,
            'championships_won': 0,
            'championships_participated': 0,
            'win_rate': 0,
            'total_championship_matches': 0,
            'championship_matches_won': 0,
            'favorite_championship_size': 0,
            'recent_championships': []
        })
    
    # Campeonatos vencidos
    championships_won = 0
    for championship in participated_championships:
        if championship.champion == user:
            championships_won += 1
    
    # Taxa de vitória em campeonatos
    win_rate = (championships_won / total_championships) * 100 if total_championships > 0 else 0
    
    # Partidas de campeonato
    championship_matches = ChampionshipMatch.objects.filter(
        championship__participants__user=user,
        match__match_players__user=user
    ).distinct()
    
    total_championship_matches = championship_matches.count()
    
    # Partidas de campeonato vencidas
    championship_matches_won = championship_matches.filter(
        match__match_players__user=user,
        match__match_players__is_winner=True
    ).count()
    
    # Tamanho de campeonato favorito
    favorite_size = participated_championships.annotate(
        participant_count=Count('participants')
    ).values('participant_count').annotate(
        count=Count('participant_count')
    ).order_by('-count').first()
    
    favorite_championship_size = favorite_size['participant_count'] if favorite_size else 0
    
    # Campeonatos recentes
    recent_championships = participated_championships.order_by('-created_at')[:5]
    
    data = {
        'total_championships': total_championships,
        'championships_won': championships_won,
        'championships_participated': total_championships,
        'win_rate': round(win_rate, 2),
        'total_championship_matches': total_championship_matches,
        'championship_matches_won': championship_matches_won,
        'favorite_championship_size': favorite_championship_size,
        'recent_championships': ChampionshipListSerializer(recent_championships, many=True).data
    }
    
    return Response(data)


class MyChampionshipsView(generics.ListAPIView):
    """Campeonatos do usuário (criados ou participando)"""
    serializer_class = ChampionshipListSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        return Championship.objects.filter(
            Q(created_by=user) | Q(participants__user=user)
        ).distinct()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def championship_leaderboard(request, championship_id):
    """Ranking de um campeonato específico"""
    championship = get_object_or_404(Championship, id=championship_id)
    
    # Calcula estatísticas dos participantes
    participants_stats = []
    
    for participant in championship.participants.all():
        user = participant.user
        
        # Partidas do usuário neste campeonato
        user_matches = ChampionshipMatch.objects.filter(
            championship=championship,
            match__match_players__user=user
        )
        
        total_matches = user_matches.count()
        wins = user_matches.filter(
            match__match_players__user=user,
            match__match_players__is_winner=True
        ).count()
        
        # Pontos totais
        total_points = sum([
            match_player.points for match_player in MatchPlayer.objects.filter(
                match__in=user_matches.values_list('match', flat=True),
                user=user
            )
        ])
        
        participants_stats.append({
            'user': {
                'id': user.id,
                'display_name': user.display_name,
                'avatar_url': user.avatar_url
            },
            'total_matches': total_matches,
            'wins': wins,
            'losses': total_matches - wins,
            'win_rate': (wins / total_matches * 100) if total_matches > 0 else 0,
            'total_points': total_points,
            'is_eliminated': participant.is_eliminated,
            'final_position': participant.final_position
        })
    
    # Ordena por vitórias e depois por pontos
    participants_stats.sort(
        key=lambda x: (x['wins'], x['total_points']),
        reverse=True
    )
    
    return Response({
        'championship': ChampionshipListSerializer(championship).data,
        'leaderboard': participants_stats
    })