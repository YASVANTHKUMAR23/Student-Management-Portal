from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.urls import path, include

from . import api_views

router = DefaultRouter()
router.register("students", api_views.StudentViewSet, basename="api-student")

urlpatterns = [

    # JWT auth
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # Account
    path("register/", api_views.RegisterView.as_view(), name="api_register"),
    path("logout/", api_views.LogoutView.as_view(), name="api_logout"),
    path("me/", api_views.MeView.as_view(), name="api_me"),

    # Resources
    path("", include(router.urls)),

]
