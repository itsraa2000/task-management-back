from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Board, BoardMembership, BoardInvitation
from users.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    board_id = serializers.PrimaryKeyRelatedField(
        source='board',
        queryset=Board.objects.all(),
        required=True,
        allow_null=False
    )
    board_name = serializers.CharField(source='board.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'start_date', 'end_date', 'created_at', 'updated_at',
            'owner', 'collaborators', 'board_id', 'board_name'
        ]

    def validate_board(self, board):
        """Ensure the user is a member of the board before allowing task creation."""
        user = self.context['request'].user
        if not BoardMembership.objects.filter(user=user, board=board).exists():
            raise serializers.ValidationError("You are not a member of this board.")
        return board

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class BoardMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role', 'joined_at']

class BoardSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(source='boardmembership_set', many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    description = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'owner', 'members', 'task_count']
    
    def get_task_count(self, obj):
        try:
            return obj.board_tasks.count()
        except AttributeError:
            # If the board_tasks relationship doesn't exist yet (before migrations)
            return 0
    
    def create(self, validated_data):
        # Set the owner to the current user
        validated_data['owner'] = self.context['request'].user
        board = super().create(validated_data)
        
        # Add the owner as a member with 'owner' role
        BoardMembership.objects.create(
            user=self.context['request'].user,
            board=board,
            role='owner'
        )
        
        return board

class BoardInvitationSerializer(serializers.ModelSerializer):
    inviter = UserSerializer(read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)
    
    class Meta:
        model = BoardInvitation
        fields = ['id', 'board', 'board_name', 'inviter', 'invitee_email', 'role', 'status', 'created_at']
        read_only_fields = ['inviter', 'status', 'created_at']
    
    def create(self, validated_data):
        # Set the inviter to the current user
        validated_data['inviter'] = self.context['request'].user
        return super().create(validated_data)

