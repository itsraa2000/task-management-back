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
    permission_classes = [permissions.IsAuthenticated, IsBoardMemberOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status', 'start_date', 'end_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Task.objects.all()

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
        if not BoardMembership.objects.filter(user=request.user, board=task.board).exists():
            return Response({"error": "Only board members can add collaborators"}, status=status.HTTP_403_FORBIDDEN)

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
    queryset = Board.objects.all()
    
    def get_queryset(self):
        return Board.objects.filter(memberships__user=self.request.user).distinct()
    
    def destroy(self, request, *args, **kwargs):
        board = self.get_object()
        
        # Delete all related objects explicitly
        board.board_tasks.all().delete()  # Delete all tasks under the board
        board.memberships.all().delete()  # Delete all board memberships
        board.invitations.all().delete()  # Delete all pending invitations
        
        board.delete()  # Finally, delete the board itself
        
        return Response({"message": "Board and all related data deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
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
        """
        Return invitations where the user is the inviter or the invitee.
        """
        user = self.request.user
        return BoardInvitation.objects.filter(models.Q(inviter=user) | models.Q(invitee_email=user.email))

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept a board invitation.
        """
        invitation = self.get_object()

        # Ensure the invitation is for the current user
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

        # Check if user already exists or create one
        try:
            user = User.objects.get(email=invitation.invitee_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User account not found. Please register before accepting the invitation.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure the user is not already a member
        if BoardMembership.objects.filter(user=user, board=invitation.board).exists():
            return Response(
                {'error': 'User is already a member of this board'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add the user to the board
        BoardMembership.objects.create(
            user=user,
            board=invitation.board,
            role=invitation.role
        )

        # Update the invitation status
        invitation.status = 'accepted'
        invitation.save()

        return Response({'status': 'Invitation accepted'})

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """
        Decline a board invitation.
        """
        invitation = self.get_object()

        # Ensure the invitation is for the current user
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

        return Response({'status': 'Invitation declined'})
    
    @action(detail=False, methods=['post'])
    def invite(self, request):
        """
        Send an invitation to a user via email and automatically add them if they have an account.
        """
        user = request.user  # The inviter
        board_id = request.data.get("board_id")
        invitee_email = request.data.get("invitee_email")
        role = request.data.get("role", "member")

        if not board_id or not invitee_email:
            return Response(
                {"error": "Board ID and invitee email are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure the board exists and the inviter is allowed to send invites
        try:
            board = Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            return Response(
                {"error": "Board not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure inviter is a board member
        if not BoardMembership.objects.filter(board=board, user=user).exists():
            return Response(
                {"error": "You do not have permission to invite users to this board."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Ensure invitee is not already a member
        if BoardMembership.objects.filter(board=board, user__email=invitee_email).exists():
            return Response(
                {"error": "User is already a member of this board."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the user already exists
        try:
            invitee = User.objects.get(email=invitee_email)
            # If the user exists, add them directly to the board
            BoardMembership.objects.create(user=invitee, board=board, role=role)
            return Response(
                {"message": "User added to the board successfully."},
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            # If the user does not exist, send an invitation
            invitation, created = BoardInvitation.objects.get_or_create(
                board=board,
                inviter=user,
                invitee_email=invitee_email,
                defaults={"role": role, "status": "pending"},
            )

            if not created:
                return Response(
                    {"error": "An invitation has already been sent to this user."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"message": "Invitation sent successfully."},
                status=status.HTTP_201_CREATED
            )