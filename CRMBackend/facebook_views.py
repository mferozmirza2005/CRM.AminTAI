"""
Facebook Integration API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
from .models import FacebookIntegration, User
from .facebook_service import FacebookGraphAPI, FacebookSyncService
from .serializers import FacebookIntegrationSerializer
import os


class FacebookIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Facebook integrations"""
    serializer_class = FacebookIntegrationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FacebookIntegration.objects.filter(user=self.request.user, is_active=True)
    
    @action(detail=False, methods=['get'])
    def oauth_url(self, request):
        """Get Facebook OAuth URL"""
        app_id = os.getenv('FACEBOOK_APP_ID', '')
        redirect_uri = request.build_absolute_uri('/api/facebook/callback/')
        scope = 'pages_manage_ads,pages_read_engagement,ads_read,leads_retrieval,business_management'
        
        oauth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={app_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_type=code"
        )
        
        return Response({"oauth_url": oauth_url})
    
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Sync Facebook data with CRM"""
        integration = self.get_object()
        
        try:
            sync_service = FacebookSyncService(integration)
            results = sync_service.sync_all(request.user)
            
            return Response({
                "message": "Sync completed successfully",
                "results": {
                    "accounts_synced": len(results["accounts"]),
                    "campaigns_synced": len(results["campaigns"]),
                    "leads_synced": len(results["leads"])
                }
            })
        except Exception as e:
            return Response(
                {"error": f"Sync failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def pages(self, request, pk=None):
        """Get Facebook Pages"""
        integration = self.get_object()
        
        try:
            api = FacebookGraphAPI(integration.access_token)
            pages = api.get_pages()
            return Response({"pages": pages})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def ad_accounts(self, request, pk=None):
        """Get Facebook Ad Accounts"""
        integration = self.get_object()
        
        try:
            api = FacebookGraphAPI(integration.access_token)
            ad_accounts = api.get_ad_accounts()
            return Response({"ad_accounts": ad_accounts})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def campaigns(self, request, pk=None):
        """Get Facebook Ad Campaigns"""
        integration = self.get_object()
        ad_account_id = request.query_params.get('ad_account_id')
        
        if not ad_account_id:
            return Response(
                {"error": "ad_account_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            api = FacebookGraphAPI(integration.access_token)
            campaigns = api.get_campaigns(ad_account_id)
            return Response({"campaigns": campaigns})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def leads(self, request, pk=None):
        """Get Facebook Leads"""
        integration = self.get_object()
        page_id = request.query_params.get('page_id')
        
        if not page_id:
            page_id = integration.facebook_page_id
        
        if not page_id:
            return Response(
                {"error": "page_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            api = FacebookGraphAPI(integration.access_token)
            lead_forms = api.get_lead_forms(page_id)
            
            all_leads = []
            for form in lead_forms:
                leads = api.get_leads(form["id"])
                all_leads.extend(leads)
            
            return Response({"leads": all_leads})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """Disconnect Facebook integration"""
        integration = self.get_object()
        integration.is_active = False
        integration.save()
        
        return Response({"message": "Facebook integration disconnected"})

