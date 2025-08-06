import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Achievement(models.Model):
    """Modelo para conquistas disponíveis no sistema"""
    
    CATEGORY_CHOICES = [
        ('habilidade', 'Habilidade'),
        ('sorte', 'Sorte'),
        ('estatistica', 'Estatística'),
        ('estrategia', 'Estratégia'),
        ('tempo', 'Tempo'),
        ('diversao', 'Diversão'),
        ('persistencia', 'Persistência'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, help_text="Código único da conquista")
    name = models.CharField(max_length=100, help_text="Nome da conquista")
    description = models.TextField(help_text="Descrição da conquista")
    icon_url = models.URLField(blank=True, null=True, help_text="URL do ícone da conquista")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, help_text="Categoria da conquista")
    points = models.PositiveIntegerField(default=10, help_text="Pontos que a conquista vale")
    is_active = models.BooleanField(default=True, help_text="Se a conquista está ativa")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'achievements'
        verbose_name = 'Conquista'
        verbose_name_plural = 'Conquistas'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def total_unlocked(self):
        """Retorna quantos usuários desbloquearam esta conquista"""
        return self.user_achievements.count()


class UserAchievement(models.Model):
    """Modelo para conquistas desbloqueadas por usuários"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    unlocked_at = models.DateTimeField(auto_now_add=True)
    match = models.ForeignKey('matches.Match', on_delete=models.SET_NULL, null=True, blank=True, 
                             help_text="Partida onde a conquista foi desbloqueada")
    
    class Meta:
        db_table = 'user_achievements'
        verbose_name = 'Conquista do Usuário'
        verbose_name_plural = 'Conquistas dos Usuários'
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.display_name} - {self.achievement.name}"