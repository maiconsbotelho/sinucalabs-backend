import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Championship(models.Model):
    """Modelo para campeonatos/torneios"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nome do campeonato")
    description = models.TextField(blank=True, help_text="Descrição do campeonato")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_championships')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(default=8, help_text="Máximo de participantes")
    
    class Meta:
        db_table = 'championships'
        verbose_name = 'Campeonato'
        verbose_name_plural = 'Campeonatos'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def total_matches(self):
        """Retorna o total de partidas do campeonato"""
        return self.championship_matches.count()
    
    @property
    def champion(self):
        """Retorna o campeão do campeonato"""
        if not self.is_finished:
            return None
        # Lógica para determinar o campeão baseado nas partidas
        # Por simplicidade, retornamos o usuário com mais vitórias
        from django.db.models import Count
        from matches.models import MatchPlayer
        
        match_ids = self.championship_matches.values_list('match_id', flat=True)
        winner = MatchPlayer.objects.filter(
            match_id__in=match_ids,
            is_winner=True
        ).values('user').annotate(
            wins=Count('user')
        ).order_by('-wins').first()
        
        if winner:
            return User.objects.get(id=winner['user'])
        return None


class ChampionshipMatch(models.Model):
    """Modelo para partidas de um campeonato"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, related_name='championship_matches')
    match = models.ForeignKey('matches.Match', on_delete=models.CASCADE, related_name='championship_matches')
    round_number = models.PositiveIntegerField(help_text="Número da rodada")
    
    class Meta:
        db_table = 'championship_matches'
        verbose_name = 'Partida do Campeonato'
        verbose_name_plural = 'Partidas do Campeonato'
        unique_together = ['championship', 'match']
        ordering = ['round_number', 'match__started_at']
    
    def __str__(self):
        return f"{self.championship.name} - Rodada {self.round_number}"


class ChampionshipParticipant(models.Model):
    """Modelo para participantes de um campeonato"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    championship = models.ForeignKey(Championship, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='championship_participations')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_eliminated = models.BooleanField(default=False)
    final_position = models.PositiveIntegerField(null=True, blank=True, help_text="Posição final no campeonato")
    
    class Meta:
        db_table = 'championship_participants'
        verbose_name = 'Participante do Campeonato'
        verbose_name_plural = 'Participantes do Campeonato'
        unique_together = ['championship', 'user']
        ordering = ['final_position', 'joined_at']
    
    def __str__(self):
        return f"{self.user.display_name} - {self.championship.name}"