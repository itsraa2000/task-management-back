from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Board, BoardMembership
from users.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'start_date', 'end_date', 'created_at', 'updated_at',
            'owner', 'collaborators'
        ]
    
    def create(self, validated_data):
        # Set the owner to the current user
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
    
    class Meta:
        model = Board
        fields = ['id', 'name', 'created_at', 'owner', 'members', 'task_count']
    
    def get_task_count(self, obj):
        return obj.tasks.count()
    
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

