from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Match, MatchPlayer, Move
from accounts.serializers import UserProfileSerializer

User = get_user_model()


class MoveSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.user.display_name', read_only=True)
    
    class Meta:
        model = Move
        fields = (
            'id', 'turn_number', 'move_type', 'points', 'description',
            'is_winning_move', 'balls_potted', 'consecutive_count',
            'time_taken_seconds', 'created_at', 'player_name'
        )
        read_only_fields = ('id', 'created_at', 'player_name')


class MatchPlayerSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    moves = MoveSerializer(many=True, read_only=True)
    
    class Meta:
        model = MatchPlayer
        fields = (
            'id', 'user', 'user_id', 'team', 'is_winner', 
            'position', 'points', 'moves'
        )
        read_only_fields = ('id', 'points')


class MatchSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    match_players = MatchPlayerSerializer(many=True)
    moves = MoveSerializer(many=True, read_only=True)
    winner = UserProfileSerializer(read_only=True)
    total_moves = serializers.ReadOnlyField()
    
    class Meta:
        model = Match
        fields = (
            'id', 'created_by', 'status', 'started_at', 'ended_at',
            'duration_minutes', 'match_players', 'moves', 'winner', 'total_moves'
        )
        read_only_fields = ('id', 'created_by', 'started_at')
    
    def create(self, validated_data):
        match_players_data = validated_data.pop('match_players')
        match = Match.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )
        
        for player_data in match_players_data:
            MatchPlayer.objects.create(match=match, **player_data)
        
        return match
    
    def update(self, instance, validated_data):
        match_players_data = validated_data.pop('match_players', [])
        
        # Atualiza os dados da partida
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualiza os jogadores se fornecido
        if match_players_data:
            for player_data in match_players_data:
                player_id = player_data.get('id')
                if player_id:
                    try:
                        player = instance.match_players.get(id=player_id)
                        for attr, value in player_data.items():
                            if attr != 'id':
                                setattr(player, attr, value)
                        player.save()
                    except MatchPlayer.DoesNotExist:
                        pass
        
        return instance


class MatchListSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    winner = UserProfileSerializer(read_only=True)
    players_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = (
            'id', 'created_by', 'status', 'started_at', 'ended_at',
            'duration_minutes', 'winner', 'players_count'
        )
    
    def get_players_count(self, obj):
        return obj.match_players.count()


class CreateMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = (
            'move_type', 'points', 'description', 'balls_potted',
            'consecutive_count', 'time_taken_seconds'
        )
    
    def create(self, validated_data):
        match = self.context['match']
        player = self.context['player']
        
        # Calcula o número do turno
        last_move = Move.objects.filter(match=match).order_by('-turn_number').first()
        turn_number = (last_move.turn_number + 1) if last_move else 1
        
        move = Move.objects.create(
            match=match,
            player=player,
            turn_number=turn_number,
            **validated_data
        )
        
        # Atualiza pontos do jogador
        player.points += validated_data.get('points', 0)
        player.save()
        
        return move


class MatchStatsSerializer(serializers.Serializer):
    total_matches = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    win_rate = serializers.FloatField()
    average_points = serializers.FloatField()
    total_moves = serializers.IntegerField()
    favorite_move_type = serializers.CharField()
    longest_match_duration = serializers.IntegerField()
    shortest_match_duration = serializers.IntegerField()