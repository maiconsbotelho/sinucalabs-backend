from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Championship, ChampionshipMatch, ChampionshipParticipant
from matches.models import Match
from accounts.serializers import UserProfileSerializer

User = get_user_model()


class ChampionshipParticipantSerializer(serializers.ModelSerializer):
    """Serializer para participantes de campeonato"""
    user = UserProfileSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = ChampionshipParticipant
        fields = [
            'id', 'user', 'user_id', 'joined_at', 
            'is_eliminated', 'final_position'
        ]
        read_only_fields = ['id', 'joined_at']


class ChampionshipMatchSerializer(serializers.ModelSerializer):
    """Serializer para partidas de campeonato"""
    match_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ChampionshipMatch
        fields = ['id', 'match', 'round_number', 'match_details']
        read_only_fields = ['id']
    
    def get_match_details(self, obj):
        from matches.serializers import MatchListSerializer
        return MatchListSerializer(obj.match).data


class ChampionshipSerializer(serializers.ModelSerializer):
    """Serializer completo para campeonatos"""
    created_by = UserProfileSerializer(read_only=True)
    participants = ChampionshipParticipantSerializer(many=True, read_only=True)
    matches = ChampionshipMatchSerializer(source='championship_matches', many=True, read_only=True)
    total_matches = serializers.ReadOnlyField()
    champion = serializers.SerializerMethodField()
    
    class Meta:
        model = Championship
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at',
            'started_at', 'ended_at', 'is_finished', 'max_participants',
            'participants', 'matches', 'total_matches', 'champion'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_champion(self, obj):
        champion = obj.champion
        if champion:
            return UserProfileSerializer(champion).data
        return None
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ChampionshipListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar campeonatos"""
    created_by = UserProfileSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    total_matches = serializers.ReadOnlyField()
    champion = serializers.SerializerMethodField()
    
    class Meta:
        model = Championship
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at',
            'started_at', 'ended_at', 'is_finished', 'max_participants',
            'participant_count', 'total_matches', 'champion'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_champion(self, obj):
        champion = obj.champion
        if champion:
            return {
                'id': champion.id,
                'display_name': champion.display_name,
                'avatar_url': champion.avatar_url
            }
        return None


class JoinChampionshipSerializer(serializers.Serializer):
    """Serializer para participar de um campeonato"""
    championship_id = serializers.UUIDField()
    
    def validate_championship_id(self, value):
        try:
            championship = Championship.objects.get(id=value)
        except Championship.DoesNotExist:
            raise serializers.ValidationError("Campeonato não encontrado.")
        
        if championship.is_finished:
            raise serializers.ValidationError("Este campeonato já foi finalizado.")
        
        if championship.started_at:
            raise serializers.ValidationError("Este campeonato já foi iniciado.")
        
        # Verifica se há vagas
        current_participants = championship.participants.count()
        if current_participants >= championship.max_participants:
            raise serializers.ValidationError("Este campeonato já atingiu o número máximo de participantes.")
        
        # Verifica se o usuário já está participando
        user = self.context['request'].user
        if championship.participants.filter(user=user).exists():
            raise serializers.ValidationError("Você já está participando deste campeonato.")
        
        return value


class CreateChampionshipMatchSerializer(serializers.Serializer):
    """Serializer para criar partida de campeonato"""
    championship_id = serializers.UUIDField()
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
        max_length=4
    )
    round_number = serializers.IntegerField(min_value=1)
    
    def validate_championship_id(self, value):
        try:
            championship = Championship.objects.get(id=value)
        except Championship.DoesNotExist:
            raise serializers.ValidationError("Campeonato não encontrado.")
        
        if championship.is_finished:
            raise serializers.ValidationError("Este campeonato já foi finalizado.")
        
        # Verifica se o usuário é o criador do campeonato
        user = self.context['request'].user
        if championship.created_by != user:
            raise serializers.ValidationError("Apenas o criador pode criar partidas no campeonato.")
        
        return value
    
    def validate_participant_ids(self, value):
        championship_id = self.initial_data.get('championship_id')
        if championship_id:
            try:
                championship = Championship.objects.get(id=championship_id)
                # Verifica se todos os participantes estão no campeonato
                championship_participant_ids = set(
                    championship.participants.values_list('user_id', flat=True)
                )
                provided_ids = set(value)
                
                if not provided_ids.issubset(championship_participant_ids):
                    raise serializers.ValidationError(
                        "Todos os participantes devem estar inscritos no campeonato."
                    )
            except Championship.DoesNotExist:
                pass  # Será validado no campo championship_id
        
        return value


class ChampionshipStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de campeonatos"""
    total_championships = serializers.IntegerField()
    championships_won = serializers.IntegerField()
    championships_participated = serializers.IntegerField()
    win_rate = serializers.FloatField()
    total_championship_matches = serializers.IntegerField()
    championship_matches_won = serializers.IntegerField()
    favorite_championship_size = serializers.IntegerField()
    recent_championships = ChampionshipListSerializer(many=True)