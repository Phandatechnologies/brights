from django.db import DatabaseError, connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    GET /api/health/

    Public endpoint that reports whether the API is running and whether it
    can reach the database. It deliberately never returns error details,
    so it cannot leak connection information.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database = "connected"
        except DatabaseError:
            database = "unavailable"

        healthy = database == "connected"
        return Response(
            {"status": "ok" if healthy else "degraded", "database": database},
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
