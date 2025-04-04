from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.db import models
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer, 
)
from .models import Profile
from tasks.models import BoardInvitation

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return Profile.objects.get(user=self.request.user)

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if query:
            return User.objects.filter(
                models.Q(username__icontains=query) | 
                models.Q(email__icontains=query) |
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query)
            )
        return User.objects.none()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_invitations(request):
    """
    Get all pending invitations for the current user
    """
    invitations = BoardInvitation.objects.filter(
        invitee_email=request.user.email,
        status='pending'
    )
    
    from tasks.serializers import BoardInvitationSerializer
    serializer = BoardInvitationSerializer(invitations, many=True)
    return Response(serializer.data)