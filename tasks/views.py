from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import models
from .models import Task, Board, BoardMembership
from .serializers import TaskSerializer, BoardSerializer
from .permissions import IsOwnerOrReadOnly, IsBoardMemberOrReadOnly

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        # Return tasks that the user owns or collaborates on
        return Task.objects.filter(
            models.Q(owner=user) | models.Q(collaborators=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def add_collaborator(self, request, pk=None):
        task = self.get_object()
        try:
            user_id = request.data.get('user_id')
            user = User.objects.get(id=user_id)
            task.collaborators.add(user)
            return Response({'status': 'collaborator added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_collaborator(self, request, pk=None):
        task = self.get_object()
        try:
            user_id = request.data.get('user_id')
            user = User.objects.get(id=user_id)
            task.collaborators.remove(user)
            return Response({'status': 'collaborator removed'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        # Return boards that the user is a member of
        return Board.objects.filter(members=user).distinct()
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        board = self.get_object()
        try:
            user_id = request.data.get('user_id')
            role = request.data.get('role', 'member')
            user = User.objects.get(id=user_id)
            
            # Check if user is already a member
            if BoardMembership.objects.filter(user=user, board=board).exists():
                return Response({'error': 'User is already a member'}, status=status.HTTP_400_BAD_REQUEST)
            
            BoardMembership.objects.create(user=user, board=board, role=role)
            return Response({'status': 'member added'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        board = self.get_object()
        try:
            user_id = request.data.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Cannot remove the owner
            membership = BoardMembership.objects.get(user=user, board=board)
            if membership.role == 'owner':
                return Response({'error': 'Cannot remove the owner'}, status=status.HTTP_400_BAD_REQUEST)
            
            membership.delete()
            return Response({'status': 'member removed'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except BoardMembership.DoesNotExist:
            return Response({'error': 'User is not a member'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_task(self, request, pk=None):
        board = self.get_object()
        try:
            task_id = request.data.get('task_id')
            task = Task.objects.get(id=task_id)
            board.tasks.add(task)
            return Response({'status': 'task added'})
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_task(self, request, pk=None):
        board = self.get_object()
        try:
            task_id = request.data.get('task_id')
            task = Task.objects.get(id=task_id)
            board.tasks.remove(task)
            return Response({'status': 'task removed'})
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)