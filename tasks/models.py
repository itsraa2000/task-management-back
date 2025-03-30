# tasks/models.py

from django.db import models
from django.contrib.auth.models import User

class Board(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, related_name="owned_boards", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def task_count(self):
        return self.board_tasks.count()  # related_name from Task model

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in-progress', 'In Progress'),
        ('done', 'Done'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(User, related_name='owned_tasks', on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(User, related_name='collaborated_tasks', blank=True)
    board = models.ForeignKey(Board, related_name='board_tasks', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

class BoardMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "board")

    def __str__(self):
        return f"{self.user.username} - {self.board.name} ({self.role})"
    
class BoardInvitation(models.Model):
    invitee_email = models.EmailField()
    role = models.CharField(
        max_length=10,
        choices=[('owner', 'Owner'), ('admin', 'Admin'), ('member', 'Member')],
        default='member'
    )
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey(Board, related_name='invitations', on_delete=models.CASCADE)
    inviter = models.ForeignKey(User, related_name='sent_invitations', on_delete=models.CASCADE)