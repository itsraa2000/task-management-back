from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, BoardViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'boards', BoardViewSet, basename='board')

urlpatterns = [
    path('', include(router.urls)),
]

