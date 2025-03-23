from django.contrib import admin
from .models import Task, Board, BoardMembership

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'status', 'owner', 'start_date', 'end_date')
    list_filter = ('priority', 'status', 'owner')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    list_filter = ('owner',)
    search_fields = ('name',)

@admin.register(BoardMembership)
class BoardMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'board', 'role', 'joined_at')
    list_filter = ('role', 'board')
    search_fields = ('user__username', 'board__name')