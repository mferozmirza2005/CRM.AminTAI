from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from django.contrib import messages

# -----------------------------
# Auth / Entry Views
# -----------------------------

@never_cache
def home_redirect(request):
    """
    Redirects root '/' to login or dashboard depending on session state.
    """
    return redirect("/dashboard")


@never_cache
def login_page(request):
    """
    Renders login page. Auth handled via JS calling /api/auth/login/.
    """
    return render(request, "login.html")


@never_cache
def signup_page(request):
    """
    Renders signup page. Registration handled via JS calling /api/auth/register/.
    """
    return render(request, "signup.html")


@never_cache
def logout_page(request):
    """
    Just renders a logout redirect view; the token is blacklisted in JS.
    """
    messages.info(request, "You have been logged out.")
    return redirect("login")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def settings_page(request):
    return render(request, "settings.html")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_management_page(request):
    return render(request, "users.html")

# -----------------------------
# Dashboard View
# -----------------------------

@never_cache
def dashboard_page(request):
    """
    Displays dashboard. JS will fetch user data via /api/dashboard/ using JWT.
    """
    return render(request, "dashboard.html")


# -----------------------------
# CRM Pages (data fetched via API)
# -----------------------------

@never_cache
def accounts_page(request):
    """
    Displays Accounts list page (data fetched via /api/accounts/).
    """
    return render(request, "accounts.html")


@never_cache
def contacts_page(request):
    """
    Displays Contacts list page (data fetched via /api/contacts/).
    """
    return render(request, "contacts.html")


@never_cache
def leads_page(request):
    """
    Displays Leads list page (data fetched via /api/leads/).
    """
    return render(request, "leads.html")


@never_cache
def deals_page(request):
    """
    Displays Deals list page (data fetched via /api/deals/).
    """
    return render(request, "deals.html")


@never_cache
def campaigns_page(request):
    """
    Displays Campaigns list page (data fetched via /api/campaigns/).
    """
    return render(request, "campaigns.html")


@never_cache
def tasks_page(request):
    """
    Displays Tasks list page (data fetched via /api/tasks/).
    """
    return render(request, "tasks.html")
