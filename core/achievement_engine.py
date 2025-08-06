from typing import List, Dict, Any
from django.contrib.auth import get_user_model
from achievements.models import Achievement, UserAchievement
from matches.models import Match, MatchPlayer, Move
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class AchievementEngine:
    """Engine responsável por avaliar e desbloquear conquistas"""
    
    def __init__(self):
        self.achievement_rules = {
            'indesnucavel': self._check_indesnucavel,
            'rei_desnuque': self._check_rei_desnuque,
            'gato_doido': self._check_gato_doido,
            'roleta_sorte': self._check_roleta_sorte,
            'relampago': self._check_relampago,
            'ceo_sinuca': self._check_ceo_sinuca,
            'taco_destino': self._check_taco_destino,
            'mestre_tatica': self._check_mestre_tatica,
            'nunca_erraram': self._check_nunca_erraram,
            'acabou_comigo': self._check_acabou_comigo,
            'zerado': self._check_zerado,
            'combo_5x': self._check_combo_5x,
            'sniper': self._check_sniper,
            'marretao': self._check_marretao,
            'tabelinha': self._check_tabelinha,
            'vira_vira': self._check_vira_vira,
            'campeao': self._check_campeao,
            'viciado': self._check_viciado,
            'colecionador': self._check_colecionador,
            'fantasma': self._check_fantasma,
            'zagueiro': self._check_zagueiro,
            'palhaco': self._check_palhaco,
            'sem_choro': self._check_sem_choro,
            'sanguenozoi': self._check_sanguenozoi,
            'testa_fria': self._check_testa_fria,
            'zen_master': self._check_zen_master,
            'alquimista': self._check_alquimista,
            'karma': self._check_karma,
            'meme_bola8': self._check_meme_bola8,
            'espirito_olimpico': self._check_espirito_olimpico,
        }
    
    def evaluate_match_achievements(self, match: Match) -> List[Dict[str, Any]]:
        """Avalia conquistas após o fim de uma partida"""
        unlocked_achievements = []
        
        for player in match.match_players.all():
            user_achievements = self.evaluate_user_achievements(player.user, match)
            unlocked_achievements.extend(user_achievements)
        
        return unlocked_achievements
    
    def evaluate_user_achievements(self, user: User, match: Match = None) -> List[Dict[str, Any]]:
        """Avalia conquistas para um usuário específico"""
        unlocked_achievements = []
        
        # Busca todas as conquistas ativas
        achievements = Achievement.objects.filter(is_active=True)
        
        for achievement in achievements:
            # Verifica se o usuário já possui esta conquista
            if UserAchievement.objects.filter(user=user, achievement=achievement).exists():
                continue
            
            # Verifica se a regra da conquista foi atendida
            rule_func = self.achievement_rules.get(achievement.code)
            if rule_func and rule_func(user, match):
                # Desbloqueia a conquista
                user_achievement = UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                    match=match
                )
                
                unlocked_achievements.append({
                    'user': user,
                    'achievement': achievement,
                    'user_achievement': user_achievement,
                    'match': match
                })
        
        return unlocked_achievements
    
    # Regras específicas para cada conquista
    
    def _check_indesnucavel(self, user: User, match: Match) -> bool:
        """Escapou de 3 snookers na mesma partida"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        
        # Conta snookers sofridos (quando o oponente fez snooker)
        snooker_escapes = Move.objects.filter(
            match=match,
            move_type='snooker'
        ).exclude(player=player).count()
        
        return snooker_escapes >= 3
    
    def _check_rei_desnuque(self, user: User, match: Match) -> bool:
        """Deu 5 snookers na mesma partida"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        
        snookers_made = Move.objects.filter(
            match=match,
            player=player,
            move_type='snooker'
        ).count()
        
        return snookers_made >= 5
    
    def _check_gato_doido(self, user: User, match: Match) -> bool:
        """Jogou tudo errado, mas venceu"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user, is_winner=True).first()
        if not player:
            return False
        
        # Verifica se teve muitos erros mas ainda ganhou
        errors = Move.objects.filter(
            match=match,
            player=player,
            move_type='erro'
        ).count()
        
        total_moves = Move.objects.filter(match=match, player=player).count()
        
        return errors >= 3 and total_moves > 5
    
    def _check_roleta_sorte(self, user: User, match: Match) -> bool:
        """Venceu jogando na sorte"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user, is_winner=True).first()
        if not player:
            return False
        
        lucky_moves = Move.objects.filter(
            match=match,
            player=player,
            move_type='na_sorte'
        ).count()
        
        return lucky_moves >= 3
    
    def _check_relampago(self, user: User, match: Match) -> bool:
        """Ganhou em menos de 3 minutos"""
        if not match or not match.duration_minutes:
            return False
        
        player = match.match_players.filter(user=user, is_winner=True).first()
        if not player:
            return False
        
        return match.duration_minutes < 3
    
    def _check_ceo_sinuca(self, user: User, match: Match) -> bool:
        """Jogou 50 partidas"""
        total_matches = MatchPlayer.objects.filter(user=user).count()
        return total_matches >= 50
    
    def _check_taco_destino(self, user: User, match: Match) -> bool:
        """Ganhou na última bola, na última jogada"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user, is_winner=True).first()
        if not player:
            return False
        
        # Verifica se a última jogada foi a vencedora
        last_move = Move.objects.filter(match=match, player=player).order_by('-turn_number').first()
        return last_move and last_move.is_winning_move
    
    def _check_mestre_tatica(self, user: User, match: Match) -> bool:
        """Eliminou só a última bola do adversário"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user, is_winner=True).first()
        if not player:
            return False
        
        # Lógica específica para verificar se eliminou apenas a última bola
        # Por simplicidade, verificamos se fez poucas jogadas mas ganhou
        player_moves = Move.objects.filter(match=match, player=player).count()
        return player_moves <= 3 and player.is_winner
    
    def _check_nunca_erraram(self, user: User, match: Match) -> bool:
        """Fez uma partida perfeita (sem erros)"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        
        errors = Move.objects.filter(
            match=match,
            player=player,
            move_type__in=['erro', 'falta']
        ).count()
        
        total_moves = Move.objects.filter(match=match, player=player).count()
        
        return errors == 0 and total_moves >= 5
    
    def _check_acabou_comigo(self, user: User, match: Match) -> bool:
        """Foi derrotado sem fazer um único ponto"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user, is_winner=False).first()
        if not player:
            return False
        
        return player.points == 0
    
    def _check_zerado(self, user: User, match: Match) -> bool:
        """Terminou a partida com 0 pontos"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        
        return player.points == 0
    
    def _check_combo_5x(self, user: User, match: Match) -> bool:
        """Acertou 5 bolas consecutivas"""
        if not match:
            return False
        
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        
        # Verifica se existe alguma jogada com consecutive_count >= 5
        combo_move = Move.objects.filter(
            match=match,
            player=player,
            consecutive_count__gte=5
        ).exists()
        
        return combo_move
    
    # Implementações simplificadas para as demais conquistas
    def _check_sniper(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_marretao(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_tabelinha(self, user: User, match: Match) -> bool:
        if not match:
            return False
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        return Move.objects.filter(match=match, player=player, move_type='tabela').count() >= 2
    
    def _check_vira_vira(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica de virada
    
    def _check_campeao(self, user: User, match: Match) -> bool:
        from championships.models import Championship
        return Championship.objects.filter(champion=user).exists()
    
    def _check_viciado(self, user: User, match: Match) -> bool:
        # Verifica se jogou todos os dias da semana
        week_ago = timezone.now() - timedelta(days=7)
        matches_this_week = MatchPlayer.objects.filter(
            user=user,
            match__started_at__gte=week_ago
        ).values('match__started_at__date').distinct().count()
        return matches_this_week >= 7
    
    def _check_colecionador(self, user: User, match: Match) -> bool:
        return UserAchievement.objects.filter(user=user).count() >= 10
    
    def _check_fantasma(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_zagueiro(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica de ponto contra
    
    def _check_palhaco(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_sem_choro(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_sanguenozoi(self, user: User, match: Match) -> bool:
        # Jogou 5 partidas seguidas
        recent_matches = MatchPlayer.objects.filter(
            user=user
        ).order_by('-match__started_at')[:5]
        
        if recent_matches.count() < 5:
            return False
        
        # Verifica se foram em sequência (sem muito tempo entre elas)
        for i in range(len(recent_matches) - 1):
            time_diff = recent_matches[i].match.started_at - recent_matches[i+1].match.started_at
            if time_diff > timedelta(hours=2):
                return False
        
        return True
    
    def _check_testa_fria(self, user: User, match: Match) -> bool:
        if not match:
            return False
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        return Move.objects.filter(
            match=match, 
            player=player, 
            time_taken_seconds__gte=10
        ).exists()
    
    def _check_zen_master(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_alquimista(self, user: User, match: Match) -> bool:
        # Ganhou 10 partidas (simplificado)
        wins = MatchPlayer.objects.filter(user=user, is_winner=True).count()
        return wins >= 10
    
    def _check_karma(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica
    
    def _check_meme_bola8(self, user: User, match: Match) -> bool:
        if not match:
            return False
        player = match.match_players.filter(user=user).first()
        if not player:
            return False
        return Move.objects.filter(
            match=match, 
            player=player, 
            move_type='mata_8',
            turn_number=1
        ).exists()
    
    def _check_espirito_olimpico(self, user: User, match: Match) -> bool:
        return False  # Implementar lógica específica


# Instância global do engine
achievement_engine = AchievementEngine()