from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Achievement, UserAchievement
from .serializers import (
    AchievementSerializer,
    UserAchievementSerializer,
    UserAchievementListSerializer,
    AchievementStatsSerializer
)


class AchievementListView(generics.ListAPIView):
    """Lista todas as conquistas disponíveis"""
    queryset = Achievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']


class UserAchievementListView(generics.ListAPIView):
    """Lista conquistas desbloqueadas pelo usuário"""
    serializer_class = UserAchievementListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['achievement__category']
    ordering = ['-unlocked_at']
    
    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)


class UserAchievementDetailView(generics.RetrieveAPIView):
    """Detalhes de uma conquista específica do usuário"""
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def achievement_stats(request):
    """Estatísticas de conquistas do usuário"""
    user = request.user
    
    # Total de conquistas disponíveis
    total_achievements = Achievement.objects.filter(is_active=True).count()
    
    # Conquistas desbloqueadas pelo usuário
    user_achievements = UserAchievement.objects.filter(user=user)
    unlocked_achievements = user_achievements.count()
    
    # Porcentagem de conclusão
    completion_percentage = (unlocked_achievements / total_achievements * 100) if total_achievements > 0 else 0
    
    # Conquistas recentes (últimas 5)
    recent_achievements = user_achievements.order_by('-unlocked_at')[:5]
    
    # Conquistas por categoria
    achievements_by_category = {}
    categories = Achievement.CATEGORY_CHOICES
    
    for category_code, category_name in categories:
        total_in_category = Achievement.objects.filter(
            category=category_code, 
            is_active=True
        ).count()
        
        unlocked_in_category = user_achievements.filter(
            achievement__category=category_code
        ).count()
        
        achievements_by_category[category_name] = {
            'total': total_in_category,
            'unlocked': unlocked_in_category,
            'percentage': (unlocked_in_category / total_in_category * 100) if total_in_category > 0 else 0
        }
    
    data = {
        'total_achievements': total_achievements,
        'unlocked_achievements': unlocked_achievements,
        'completion_percentage': round(completion_percentage, 2),
        'recent_achievements': UserAchievementListSerializer(recent_achievements, many=True).data,
        'achievements_by_category': achievements_by_category
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def leaderboard(request):
    """Ranking de usuários por conquistas"""
    from django.contrib.auth import get_user_model
    from accounts.serializers import UserProfileSerializer
    
    User = get_user_model()
    
    # Usuários com mais conquistas
    users_with_achievements = User.objects.annotate(
        achievement_count=Count('user_achievements')
    ).filter(
        achievement_count__gt=0
    ).order_by('-achievement_count')[:10]
    
    leaderboard_data = []
    for i, user in enumerate(users_with_achievements, 1):
        user_data = UserProfileSerializer(user).data
        user_data['position'] = i
        user_data['achievement_count'] = user.achievement_count
        leaderboard_data.append(user_data)
    
    return Response({
        'leaderboard': leaderboard_data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def achievement_progress(request, achievement_id):
    """Progresso do usuário em uma conquista específica"""
    try:
        achievement = Achievement.objects.get(id=achievement_id, is_active=True)
    except Achievement.DoesNotExist:
        return Response(
            {'error': 'Conquista não encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    user = request.user
    
    # Verifica se o usuário já possui a conquista
    user_achievement = UserAchievement.objects.filter(
        user=user, 
        achievement=achievement
    ).first()
    
    if user_achievement:
        return Response({
            'achievement': AchievementSerializer(achievement).data,
            'unlocked': True,
            'unlocked_at': user_achievement.unlocked_at,
            'progress': 100
        })
    
    # Para conquistas não desbloqueadas, retorna progresso básico
    # Aqui você pode implementar lógica específica para cada tipo de conquista
    progress = 0
    
    # Exemplo: para conquista de número de partidas
    if achievement.code == 'ceo_sinuca':
        total_matches = user.total_matches
        progress = min((total_matches / 50) * 100, 100)
    
    return Response({
        'achievement': AchievementSerializer(achievement).data,
        'unlocked': False,
        'progress': round(progress, 2)
    })