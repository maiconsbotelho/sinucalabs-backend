import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Match(models.Model):
    """Modelo para partidas de sinuca"""
    
    STATUS_CHOICES = [
        ('em_andamento', 'Em Andamento'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Duração da partida em minutos")
    
    class Meta:
        db_table = 'matches'
        verbose_name = 'Partida'
        verbose_name_plural = 'Partidas'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Partida {self.id} - {self.status}"
    
    @property
    def winner(self):
        """Retorna o jogador vencedor da partida"""
        winner_player = self.match_players.filter(is_winner=True).first()
        return winner_player.user if winner_player else None
    
    @property
    def total_moves(self):
        """Retorna o total de jogadas da partida"""
        return self.moves.count()
    
    def clean(self):
        if self.status == 'finalizada' and not self.ended_at:
            raise ValidationError('Partida finalizada deve ter data de término.')


class MatchPlayer(models.Model):
    """Modelo para jogadores em uma partida"""
    
    TEAM_CHOICES = [
        ('A', 'Time A'),
        ('B', 'Time B'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='match_players')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_players')
    team = models.CharField(max_length=1, choices=TEAM_CHOICES)
    is_winner = models.BooleanField(default=False)
    position = models.PositiveIntegerField(help_text="Ordem de jogada")
    points = models.PositiveIntegerField(default=0, help_text="Pontos do jogador na partida")
    
    class Meta:
        db_table = 'match_players'
        verbose_name = 'Jogador da Partida'
        verbose_name_plural = 'Jogadores da Partida'
        unique_together = ['match', 'user']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.user.display_name} - {self.match.id}"


class Move(models.Model):
    """Modelo para jogadas em uma partida"""
    
    MOVE_TYPE_CHOICES = [
        ('normal', 'Jogada Normal'),
        ('falta', 'Falta'),
        ('snooker', 'Snooker'),
        ('mata_8', 'Mata Bola 8'),
        ('erro', 'Erro'),
        ('na_sorte', 'Na Sorte'),
        ('tabela', 'Tabela'),
        ('combo', 'Combo'),
        ('perfect', 'Jogada Perfeita'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='moves')
    player = models.ForeignKey(MatchPlayer, on_delete=models.CASCADE, related_name='moves')
    turn_number = models.PositiveIntegerField(help_text="Número do turno")
    move_type = models.CharField(max_length=30, choices=MOVE_TYPE_CHOICES)
    points = models.IntegerField(default=0, help_text="Pontos ganhos/perdidos na jogada")
    description = models.TextField(blank=True, help_text="Descrição da jogada")
    is_winning_move = models.BooleanField(default=False, help_text="Se foi a jogada que venceu a partida")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Campos específicos para análise de conquistas
    balls_potted = models.PositiveIntegerField(default=0, help_text="Bolas encaçapadas")
    consecutive_count = models.PositiveIntegerField(default=0, help_text="Contador de jogadas consecutivas")
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Tempo gasto na jogada")
    
    class Meta:
        db_table = 'moves'
        verbose_name = 'Jogada'
        verbose_name_plural = 'Jogadas'
        ordering = ['turn_number', 'created_at']
    
    def __str__(self):
        return f"Jogada {self.turn_number} - {self.player.user.display_name} - {self.move_type}"