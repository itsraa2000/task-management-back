from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .models import Task, Board, BoardMembership, BoardInvitation
from .serializers import TaskSerializer, BoardSerializer, BoardInvitationSerializer
from .permissions import IsOwnerOrReadOnly, IsBoardMemberOrReadOnly

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status', 'start_date', 'end_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Return tasks that the user owns or collaborates on
        return Task.objects.filter(
            models.Q(owner=user) | models.Q(collaborators=user)
        ).distinct()
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        Get tasks for calendar view with date filtering
        """
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = Task.objects.filter(
            models.Q(owner=user) | models.Q(collaborators=user)
        )
        
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming tasks (next 7 days)
        """
        user = request.user
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        queryset = Task.objects.filter(
            (models.Q(owner=user) | models.Q(collaborators=user)) &
            (models.Q(start_date__gte=today, start_date__lte=next_week) | 
             models.Q(end_date__gte=today, end_date__lte=next_week))
        ).distinct()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        # Return boards that the user is a member of
        return Board.objects.filter(members=user).distinct()
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Get all tasks for a specific board
        """
        board = self.get_object()
        tasks = board.board_tasks.all()
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)
    
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
    def invite_user(self, request, pk=None):
        """
        Invite a user to the board by email
        """
        board = self.get_object()
        
        # Check if the current user has permission to invite
        try:
            membership = BoardMembership.objects.get(user=request.user, board=board)
            if membership.role not in ['owner', 'admin']:
                return Response(
                    {'error': 'You do not have permission to invite users'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except BoardMembership.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this board'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BoardInvitationSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Check if invitation already exists
            invitee_email = serializer.validated_data['invitee_email']
            if BoardInvitation.objects.filter(
                board=board, 
                invitee_email=invitee_email, 
                status='pending'
            ).exists():
                return Response(
                    {'error': 'An invitation is already pending for this email'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user is already a member
            try:
                user = User.objects.get(email=invitee_email)
                if BoardMembership.objects.filter(user=user, board=board).exists():
                    return Response(
                        {'error': 'User is already a member of this board'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except User.DoesNotExist:
                # User doesn't exist yet, which is fine
                pass
            
            invitation = serializer.save(board=board, inviter=request.user)
            
            # In a real app, you would send an email here
            # For now, we'll just return the invitation
            return Response(
                BoardInvitationSerializer(invitation).data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BoardInvitationViewSet(viewsets.ModelViewSet):
    serializer_class = BoardInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Return invitations sent by the user
        return BoardInvitation.objects.filter(inviter=user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept an invitation (for testing purposes)
        In a real app, this would be handled via email links
        """
        invitation = self.get_object()
        
        # Check if the invitation is for the current user
        if invitation.invitee_email != request.user.email:
            return Response(
                {'error': 'This invitation is not for you'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the invitation is still pending
        if invitation.status != 'pending':
            return Response(
                {'error': f'Invitation has already been {invitation.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add the user to the board
        BoardMembership.objects.create(
            user=request.user,
            board=invitation.board,
            role=invitation.role
        )
        
        # Update the invitation status
        invitation.status = 'accepted'
        invitation.save()
        
        return Response({'status': 'invitation accepted'})
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """
        Decline an invitation
        """
        invitation = self.get_object()
        
        # Check if the invitation is for the current user
        if invitation.invitee_email != request.user.email:
            return Response(
                {'error': 'This invitation is not for you'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the invitation is still pending
        if invitation.status != 'pending':
            return Response(
                {'error': f'Invitation has already been {invitation.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the invitation status
        invitation.status = 'declined'
        invitation.save()
        
        return Response({'status': 'invitation declined'})