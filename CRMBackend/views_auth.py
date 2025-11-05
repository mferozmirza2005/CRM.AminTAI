from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .serializers import RegisterSerializer, CRMSettingsSerializer
from .models import Account, Contact, Lead, Deal, Campaign, Task
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from .models import User, CRMSettings
from django.conf import settings
from django.urls import reverse

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        role = serializer.validated_data.get("role", User.Role.EMPLOYEE)
        request_user = self.request.user if self.request.user.is_authenticated else None
        if role in (User.Role.ADMIN, User.Role.SUPERADMIN) and (
            not request_user or request_user.role != User.Role.SUPERADMIN
        ):
            raise PermissionError("Only SuperAdmin can create Admin/SuperAdmin users.")
        serializer.save()


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        user = authenticate(email=request.data.get("email"), password=request.data.get("password"))
        if user:
            login(request, user)
        return response


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "email required"}, status=400)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "detail": "If an account with that email exists, a reset link has been sent."
                }
            )
        token = token_generator.make_token(user)
        uid = user.pk
        reset_path = reverse("password-reset-confirm")
        reset_url = f"{request.scheme}://{request.get_host()}{reset_path}?uid={uid}&token={token}"
        send_mail(
            "Password reset",
            f"Use this link to reset your password: {reset_url}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return Response(
            {
                "detail": "If an account with that email exists, a reset link has been sent."
            }
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("password")
        if not all([uid, token, new_password]):
            return Response({"detail": "uid, token and password required."}, status=400)
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=400)
        if not token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset successful."})


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Normalize role to values expected by frontend (superuser/admin/employee)
        role_raw = getattr(user, "role", "EMPLOYEE")
        if getattr(user, "is_superuser", False) or str(role_raw).upper() == "SUPERADMIN":
            role = "superuser"
        elif str(role_raw).upper() == "ADMIN":
            role = "admin"
        else:
            role = "employee"

        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        total_leads = Lead.objects.count()
        total_deals = Deal.objects.count()

        # Core totals
        data = {
            "role": role,
            "total_accounts": Account.objects.count(),
            "total_contacts": Contact.objects.count(),
            "total_leads": total_leads,
            "total_deals": total_deals,
            "total_campaigns": Campaign.objects.count(),
            "total_tasks": Task.objects.count(),
        }

        # Totals and recent KPIs
        data["total_deal_value"] = (
            Deal.objects.aggregate(v=Sum("amount"))[("v")] or 0
        )
        data["recent_deals_7d"] = Deal.objects.filter(created_at__gte=last_7_days).count()

        # Deal stages distribution
        stage_counts_qs = (
            Deal.objects.values("stage").order_by("stage").annotate(count=Count("id"))
        )
        data["deal_stages"] = {row["stage"]: row["count"] for row in stage_counts_qs}

        # Lead statuses distribution
        lead_status_qs = (
            Lead.objects.values("status").order_by("status").annotate(count=Count("id"))
        )
        data["lead_statuses"] = {row["status"]: row["count"] for row in lead_status_qs}

        # Conversion rate: percentage of leads that are CONVERTED
        converted_leads = data["lead_statuses"].get("CONVERTED", 0)
        data["conversion_rate"] = int(round((converted_leads / total_leads) * 100)) if total_leads else 0

        # Deal value by stage
        stage_value_qs = (
            Deal.objects.values("stage").order_by("stage").annotate(total=Sum("amount"))
        )
        data["deal_value_by_stage"] = {row["stage"]: float(row["total"]) if row["total"] else 0 for row in stage_value_qs}

        # Trends over last 30 days: weekly buckets (4 weeks)
        # Build 4 weekly ranges ending today: [W-3, W-2, W-1, W]
        trends = []
        for i in range(4, 0, -1):
            period_start = now - timedelta(days=i * 7)
            period_end = now - timedelta(days=(i - 1) * 7)
            trends.append({
                "week": f"Week {5 - i}",
                "accounts": Account.objects.filter(created_at__gte=period_start, created_at__lt=period_end).count(),
                "leads": Lead.objects.filter(created_at__gte=period_start, created_at__lt=period_end).count(),
                "deals": Deal.objects.filter(created_at__gte=period_start, created_at__lt=period_end).count(),
            })
        data["trends"] = trends

        # Campaign performance: leads per campaign + budget (top 5 by leads)
        campaign_lead_counts = (
            Campaign.objects
            .annotate(lead_count=Count("leads"))
            .order_by("-lead_count", "-budget")
            .values("id", "name", "budget", "lead_count")[:5]
        )
        data["campaign_performance"] = list(campaign_lead_counts)

        # Include previews by role
        if role == "superuser":
            data["recent_campaigns"] = list(
                Campaign.objects.order_by("-created_at")[:5].values(
                    "id", "name", "budget", "created_at"
                )
            )
            data["recent_leads"] = list(
                Lead.objects.order_by("-created_at")[:5].values(
                    "id", "title", "status", "created_at"
                )
            )
            data["recent_deals"] = list(
                Deal.objects.order_by("-created_at")[:5].values(
                    "id", "title", "amount", "stage", "created_at"
                )
            )
        elif role == "admin":
            data["recent_accounts"] = list(
                Account.objects.order_by("-created_at")[:5].values(
                    "id", "name", "region", "created_at"
                )
            )
            data["recent_leads"] = list(
                Lead.objects.order_by("-created_at")[:5].values(
                    "id", "title", "status", "created_at"
                )
            )
        elif role == "employee":
            data["assigned_leads"] = list(
                Lead.objects.filter(owner=user).values(
                    "id", "title", "status", "created_at"
                )
            )
            data["assigned_tasks"] = list(
                Task.objects.filter(assigned_to=user).values(
                    "id", "title", "due_date", "completed", "created_at"
                )
            )

        return Response(data)


class SettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Return current CRM settings"""
        settings_obj, _ = CRMSettings.objects.get_or_create(id=1)
        serializer = CRMSettingsSerializer(settings_obj)
        return Response(serializer.data)

    def post(self, request):
        """Update CRM settings"""
        settings_obj, _ = CRMSettings.objects.get_or_create(id=1)
        serializer = CRMSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "ok", "message": "Settings updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
