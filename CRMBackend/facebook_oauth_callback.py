"""
Facebook OAuth Callback View - handles redirect from Facebook
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import FacebookIntegration
from .facebook_service import FacebookGraphAPI
import os
import requests


@method_decorator(csrf_exempt, name='dispatch')
class FacebookOAuthCallbackView(APIView):
    """Handle Facebook OAuth callback redirect"""
    
    def get(self, request):
        """Handle GET request from Facebook redirect"""
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            # Redirect to frontend with error
            error_description = request.GET.get('error_description', 'Authentication failed')
            return redirect(f'/dashboard/facebook/?error={error}&error_description={error_description}')
        
        if not code:
            return redirect('/dashboard/facebook/?error=no_code')
        
        # For authenticated users, process the callback
        if request.user.is_authenticated:
            try:
                app_id = os.getenv('FACEBOOK_APP_ID', '')
                app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
                redirect_uri = request.build_absolute_uri('/api/facebook/callback/')
                
                # Exchange code for access token
                token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
                token_params = {
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "redirect_uri": redirect_uri,
                    "code": code
                }
                
                token_response = requests.get(token_url, params=token_params)
                token_response.raise_for_status()
                token_data = token_response.json()
                
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 0)
                
                if not access_token:
                    return redirect('/dashboard/facebook/?error=no_token')
                
                # Get user info
                api = FacebookGraphAPI(access_token)
                user_info = api.get_user_info()
                
                # Create or update integration
                FacebookIntegration.objects.update_or_create(
                    user=request.user,
                    defaults={
                        "access_token": access_token,
                        "token_expires_at": timezone.now() + timezone.timedelta(seconds=expires_in) if expires_in else None,
                        "facebook_user_id": user_info.get("id", ""),
                        "is_active": True,
                        "last_synced_at": timezone.now()
                    }
                )
                
                return redirect('/dashboard/facebook/?success=connected')
                
            except Exception as e:
                return redirect(f'/dashboard/facebook/?error=processing_error&message={str(e)}')
        else:
            # Store code in session and redirect to login
            request.session['facebook_oauth_code'] = code
            return redirect('/login/?next=/dashboard/facebook/')

