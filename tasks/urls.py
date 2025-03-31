from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, BoardViewSet, BoardInvitationViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='tasks')
router.register(r'boards', BoardViewSet, basename='boards')
router.register(r'invitations', BoardInvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
]