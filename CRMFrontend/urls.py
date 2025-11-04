from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    path('logout/', views.logout_page, name='logout'),
    path('dashboard/', views.dashboard_page, name='dashboard'),

    path('dashboard/users/', views.user_management_page, name='user_management'),
    path('dashboard/settings/', views.settings_page, name='settings'),

    # Optional placeholders for CRM modules (to extend later)
    path('dashboard/accounts/', views.accounts_page, name='accounts'),
    path('dashboard/contacts/', views.contacts_page, name='contacts'),
    path('dashboard/leads/', views.leads_page, name='leads'),
    path('dashboard/deals/', views.deals_page, name='deals'),
    path('dashboard/campaigns/', views.campaigns_page, name='campaigns'),
    path('dashboard/tasks/', views.tasks_page, name='tasks'),
]
