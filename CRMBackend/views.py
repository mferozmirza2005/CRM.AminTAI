from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import User, Account, Contact, Lead, Deal, Campaign, Task
from .serializers import (
    UserSerializer,
    AccountSerializer,
    ContactSerializer,
    LeadSerializer,
    DealSerializer,
    CampaignSerializer,
    TaskSerializer,
)
from .permissions import IsAdminOrOwner

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(region__icontains=q))
        owner = self.request.query_params.get('owner')
        if owner:
            qs = qs.filter(owner_id=owner)
        return qs.order_by('-created_at')

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(email__icontains=q) |
                Q(phone__icontains=q)
            )
        account = self.request.query_params.get('account')
        if account:
            qs = qs.filter(account_id=account)
        return qs.order_by('-created_at')

class LeadViewSet(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        owner = self.request.query_params.get('owner')
        if owner:
            qs = qs.filter(owner_id=owner)
        campaign = self.request.query_params.get('campaign')
        if campaign:
            qs = qs.filter(campaign_id=campaign)
        return qs.order_by('-created_at')

class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q))
        stage = self.request.query_params.get('stage')
        if stage:
            qs = qs.filter(stage=stage)
        account = self.request.query_params.get('account')
        if account:
            qs = qs.filter(account_id=account)
        owner = self.request.query_params.get('owner')
        if owner:
            qs = qs.filter(owner_id=owner)
        return qs.order_by('-created_at')

class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return qs.order_by('-created_at')

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        completed = self.request.query_params.get('completed')
        if completed in ('true','false'):
            qs = qs.filter(completed=(completed == 'true'))
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        return qs.order_by('-created_at')


class UserViewSet(viewsets.ModelViewSet):
    """Expose users via API at /api/users/"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs.order_by('-created_at')
