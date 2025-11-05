"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from CRMBackend import views, views_auth, facebook_views
from CRMBackend.facebook_oauth_callback import FacebookOAuthCallbackView
from CRMFrontend import urls as CRMFrontendUrls
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'contacts', views.ContactViewSet, basename='contact')
router.register(r'leads', views.LeadViewSet, basename='lead')
router.register(r'deals', views.DealViewSet, basename='deal')
router.register(r'campaigns', views.CampaignViewSet, basename='campaign')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'facebook/integrations', facebook_views.FacebookIntegrationViewSet, basename='facebook-integration')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', views_auth.RegisterView.as_view(), name='auth-register'),
    path('api/auth/login/', views_auth.LoginView.as_view(), name='token_obtain_pair'),
    path('api/auth/logout/', views_auth.LogoutView.as_view(), name='auth-logout'),
    path('api/auth/password-reset/', views_auth.PasswordResetRequestView.as_view(), name='password-reset'),
    path('api/auth/password-reset-confirm/', views_auth.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('api/dashboard/', views_auth.DashboardView.as_view(), name='dashboard'),
    path('api/settings/', views_auth.SettingsView.as_view(), name='api-settings'),

    path('', include(CRMFrontendUrls)),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('api/auth/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Facebook OAuth callback (handles redirect from Facebook)
    path('api/facebook/callback/', FacebookOAuthCallbackView.as_view(), name='facebook-callback'),
]
