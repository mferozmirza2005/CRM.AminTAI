from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone


# =========================
# Custom User
# =========================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.SUPERADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Admin"
        ADMIN = "ADMIN", "Admin"
        EMPLOYEE = "EMPLOYEE", "Employee"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    region = models.CharField(max_length=64, blank=True, null=True)
    allowed_accounts = models.ManyToManyField(
        "Account", blank=True, related_name="users"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"


# =========================
# Settings
# =========================
class CRMSettings(models.Model):
    """Global CRM configuration editable by Super Admin"""

    organization_name = models.CharField(max_length=255, default="AminTAI CRM")
    support_email = models.EmailField(default="support@example.com")
    timezone = models.CharField(max_length=100, default="UTC")
    language = models.CharField(max_length=50, default="en")
    theme_mode = models.CharField(
        max_length=20,
        choices=[("light", "Light"), ("dark", "Dark"), ("auto", "Auto")],
        default="light",
    )
    accent_color = models.CharField(max_length=10, default="#0d6efd")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CRM Settings"
        verbose_name_plural = "CRM Settings"

    def __str__(self):
        return self.organization_name


# =========================
# Account & Contact
# =========================
class Account(models.Model):
    """A company or organization you do business with."""

    name = models.CharField(max_length=255)
    region = models.CharField(max_length=64, blank=True, null=True)
    owner = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="accounts"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Contact(models.Model):
    """A person who works at an account (customer contact)."""

    account = models.ForeignKey(
        Account, related_name="contacts", on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# =========================
# Campaigns
# =========================
class Campaign(models.Model):
    """Marketing campaign that generates leads."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="campaigns"
    )
    accounts = models.ManyToManyField(Account, blank=True, related_name="campaigns")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


# =========================
# Leads
# =========================
class Lead(models.Model):
    """Potential sales opportunity from a campaign or contact."""

    STATUS = (
        ("NEW", "New"),
        ("CONTACTED", "Contacted"),
        ("QUALIFIED", "Qualified"),
        ("CONVERTED", "Converted"),
        ("LOST", "Lost"),
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="NEW")
    owner = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    campaign = models.ForeignKey(
        Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    contact = models.ForeignKey(
        Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


# =========================
# Deals
# =========================
class Deal(models.Model):
    """Sales opportunity typically converted from a qualified lead."""

    STAGE = (
        ("PROSPECT", "Prospect"),
        ("QUALIFICATION", "Qualification"),
        ("PROPOSAL", "Proposal"),
        ("NEGOTIATION", "Negotiation"),
        ("WON", "Won"),
        ("LOST", "Lost"),
    )
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stage = models.CharField(max_length=20, choices=STAGE, default="PROSPECT")
    account = models.ForeignKey(Account, related_name="deals", on_delete=models.CASCADE)
    lead = models.ForeignKey(
        Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals"
    )
    contact = models.ForeignKey(
        Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals"
    )
    owner = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals"
    )
    campaign = models.ForeignKey(
        Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="deals"
    )
    close_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} ({self.stage})"


# =========================
# Tasks / Activities
# =========================
class Task(models.Model):
    """Action items linked to any entity (Lead, Deal, Campaign, Account)."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    related_lead = models.ForeignKey(
        Lead, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    related_deal = models.ForeignKey(
        Deal, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    related_campaign = models.ForeignKey(
        Campaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    related_account = models.ForeignKey(
        Account, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
