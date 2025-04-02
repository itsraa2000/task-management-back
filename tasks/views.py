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
    
    @action(detail=False, methods=['get'])
    def test_api(self, request):
         return Response({"message": "API is working!"}, status=status.HTTP_200_OK)

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

class BoardInvitationViewSet(viewsets.ModelViewSet):
    serializer_class = BoardInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return invitations where the user is the inviter or the invitee.
        """
        user = self.request.user
        return BoardInvitation.objects.filter(models.Q(inviter=user) | models.Q(invitee_email=user.email))
    
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