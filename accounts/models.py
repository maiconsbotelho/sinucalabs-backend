import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100)
    avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'display_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return self.display_name or self.email
    
    @property
    def total_matches(self):
        """Retorna o total de partidas jogadas pelo usuário"""
        return self.match_players.count()
    
    @property
    def total_wins(self):
        """Retorna o total de vitórias do usuário"""
        return self.match_players.filter(is_winner=True).count()
    
    @property
    def total_achievements(self):
        """Retorna o total de conquistas desbloqueadas"""
        return self.user_achievements.count()
    
    @property
    def win_rate(self):
        """Retorna a taxa de vitórias do usuário"""
        if self.total_matches == 0:
            return 0
        return (self.total_wins / self.total_matches) * 100