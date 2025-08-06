from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Registro de novo usuário"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'message': 'Usuário criado com sucesso!',
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
        
        # Definir cookies httpOnly
        response.set_cookie(
            'refresh_token',
            str(refresh),
            max_age=60 * 60 * 24 * 7,  # 7 dias
            httponly=True,
            secure=False,  # True em produção com HTTPS
            samesite='Lax'
        )
        response.set_cookie(
            'access_token',
            str(refresh.access_token),
            max_age=60 * 5,  # 5 minutos
            httponly=True,
            secure=False,  # True em produção com HTTPS
            samesite='Lax'
        )
        
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """Login do usuário"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'message': 'Login realizado com sucesso!',
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_200_OK)
        
        # Definir cookies httpOnly
        response.set_cookie(
            'refresh_token',
            str(refresh),
            max_age=60 * 60 * 24 * 7,  # 7 dias
            httponly=True,
            secure=False,  # True em produção com HTTPS
            samesite='Lax'
        )
        response.set_cookie(
            'access_token',
            str(refresh.access_token),
            max_age=60 * 5,  # 5 minutos
            httponly=True,
            secure=False,  # True em produção com HTTPS
            samesite='Lax'
        )
        
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """Logout do usuário"""
    response = Response({
        'message': 'Logout realizado com sucesso!'
    }, status=status.HTTP_200_OK)
    
    # Limpar cookies
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response


class ProfileView(generics.RetrieveUpdateAPIView):
    """Visualizar e atualizar perfil do usuário"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH' or self.request.method == 'PUT':
            return UserUpdateSerializer
        return UserProfileSerializer


class UserListView(generics.ListAPIView):
    """Lista de usuários para busca"""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['display_name', 'email', 'username']
    ordering = ['-created_at']