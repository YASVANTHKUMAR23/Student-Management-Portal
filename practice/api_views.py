from rest_framework import generics, permissions, viewsets, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django_filters.rest_framework import DjangoFilterBackend

from .models import Student
from .serializers import RegisterSerializer, StudentSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/register/  — create a new account (no auth required)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class LogoutView(APIView):
    """POST /api/logout/  — blacklists the given refresh token so it (and
    any tokens rotated from it) can no longer be used to obtain new access
    tokens. Requires ``{"refresh": "<refresh token>"}`` in the body."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "The 'refresh' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Token is invalid or already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """GET /api/me/ — the currently authenticated user's own profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    """Full CRUD for students, JWT-protected.

    Provides (via the router):
        GET    /api/students/          list (paginated, searchable, filterable)
        POST   /api/students/          create
        GET    /api/students/{id}/     retrieve
        PUT    /api/students/{id}/     update
        PATCH  /api/students/{id}/     partial update
        DELETE /api/students/{id}/     delete
    """

    queryset = Student.objects.all().order_by("-created_at")
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["course", "city"]
    search_fields = ["name", "email", "city", "course"]
    ordering_fields = ["name", "age", "created_at"]
