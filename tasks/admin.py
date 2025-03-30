from django.contrib import admin
from .models import Task, Board, BoardMembership, BoardInvitation

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'status', 'owner', 'start_date', 'end_date', 'board')
    list_filter = ('priority', 'status', 'owner', 'board')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    raw_id_fields = ('owner', 'collaborators', 'board')

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name', 'description')
    raw_id_fields = ('owner',)  # Removed 'members' as it's a ManyToMany through field

@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'board', 'role', 'joined_at')
    list_filter = ('role', 'board')
    search_fields = ('user__username', 'board__name')
    raw_id_fields = ('user', 'board')

@admin.register(BoardInvitation)
class BoardInvitationAdmin(admin.ModelAdmin):
    list_display = ('board', 'inviter', 'invitee_email', 'role', 'status', 'created_at')
    list_filter = ('status', 'role', 'board')
    search_fields = ('invitee_email', 'board__name')
    raw_id_fields = ('board', 'inviter')

