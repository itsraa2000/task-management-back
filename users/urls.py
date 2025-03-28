from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView, UserDetailView, ProfileView, 
    ChangePasswordView, UserSearchView, my_invitations
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('invitations/', my_invitations, name='my-invitations'),
]