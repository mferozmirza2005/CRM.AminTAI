"""
Facebook Graph API Service for CRM Integration
"""
import requests
import json
from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, List, Optional, Any
from .models import FacebookIntegration, Account, Contact, Campaign, Lead, Deal, User


class FacebookGraphAPI:
    """Service class for interacting with Facebook Graph API"""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """Make a request to Facebook Graph API"""
        url = f"{self.BASE_URL}/{endpoint}"
        request_params = {"access_token": self.access_token}
        if params:
            request_params.update(params)
        
        try:
            if method == "GET":
                response = requests.get(url, params=request_params, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, params=request_params, json=data, headers=self.headers)
            elif method == "DELETE":
                response = requests.delete(url, params=request_params, headers=self.headers)
            else:
                response = requests.request(method, url, params=request_params, json=data, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Facebook API Error: {str(e)}")
            if hasattr(e.response, 'json'):
                error_data = e.response.json()
                raise Exception(f"Facebook API Error: {error_data.get('error', {}).get('message', str(e))}")
            raise
    
    def get_user_info(self) -> Dict:
        """Get authenticated user information"""
        return self._make_request("me", params={"fields": "id,name,email"})
    
    def get_pages(self) -> List[Dict]:
        """Get Facebook Pages managed by the user"""
        response = self._make_request("me/accounts", params={"fields": "id,name,access_token,category"})
        return response.get("data", [])
    
    def get_ad_accounts(self) -> List[Dict]:
        """Get Facebook Ad Accounts"""
        response = self._make_request("me/adaccounts", params={"fields": "id,name,account_id,currency"})
        return response.get("data", [])
    
    def get_campaigns(self, ad_account_id: str) -> List[Dict]:
        """Get Facebook Ad Campaigns"""
        response = self._make_request(
            f"{ad_account_id}/campaigns",
            params={"fields": "id,name,status,objective,start_time,end_time,daily_budget,lifetime_budget"}
        )
        return response.get("data", [])
    
    def get_ads(self, campaign_id: str) -> List[Dict]:
        """Get Ads in a campaign"""
        response = self._make_request(
            f"{campaign_id}/ads",
            params={"fields": "id,name,status,creative"}
        )
        return response.get("data", [])
    
    def get_lead_forms(self, page_id: str) -> List[Dict]:
        """Get Lead Forms for a page"""
        response = self._make_request(
            f"{page_id}/leadgen_forms",
            params={"fields": "id,name,status,leads_count"}
        )
        return response.get("data", [])
    
    def get_leads(self, lead_form_id: str) -> List[Dict]:
        """Get leads from a lead form"""
        response = self._make_request(
            f"{lead_form_id}/leads",
            params={"fields": "id,created_time,field_data"}
        )
        return response.get("data", [])
    
    def get_page_insights(self, page_id: str, since: str = None, until: str = None) -> Dict:
        """Get page insights"""
        params = {
            "metric": "page_fans,page_engaged_users,page_post_engagements",
            "period": "day"
        }
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        return self._make_request(f"{page_id}/insights", params=params)


class FacebookSyncService:
    """Service for syncing Facebook data with CRM"""
    
    def __init__(self, integration: FacebookIntegration):
        self.integration = integration
        self.api = FacebookGraphAPI(integration.access_token)
    
    def sync_accounts_from_pages(self, user: User) -> List[Account]:
        """Sync Facebook Pages as CRM Accounts"""
        pages = self.api.get_pages()
        synced_accounts = []
        
        for page_data in pages:
            account, created = Account.objects.get_or_create(
                facebook_page_id=page_data["id"],
                defaults={
                    "name": page_data.get("name", "Facebook Page"),
                    "owner": user,
                    "region": page_data.get("category", ""),
                    "facebook_synced_at": timezone.now()
                }
            )
            if not created:
                account.name = page_data.get("name", account.name)
                account.facebook_synced_at = timezone.now()
                account.save()
            
            synced_accounts.append(account)
        
        return synced_accounts
    
    def sync_campaigns_from_facebook(self, user: User, ad_account_id: str) -> List[Campaign]:
        """Sync Facebook Ad Campaigns as CRM Campaigns"""
        fb_campaigns = self.api.get_campaigns(ad_account_id)
        synced_campaigns = []
        
        for fb_campaign in fb_campaigns:
            # Parse budget
            budget = 0
            if "daily_budget" in fb_campaign:
                budget = float(fb_campaign["daily_budget"]) / 100  # Convert cents to dollars
            elif "lifetime_budget" in fb_campaign:
                budget = float(fb_campaign["lifetime_budget"]) / 100
            
            # Parse dates
            start_date = None
            end_date = None
            if fb_campaign.get("start_time"):
                start_date = datetime.fromisoformat(fb_campaign["start_time"].replace("Z", "+00:00")).date()
            if fb_campaign.get("end_time"):
                end_date = datetime.fromisoformat(fb_campaign["end_time"].replace("Z", "+00:00")).date()
            
            campaign, created = Campaign.objects.get_or_create(
                facebook_campaign_id=fb_campaign["id"],
                defaults={
                    "name": fb_campaign.get("name", "Facebook Campaign"),
                    "description": f"Objective: {fb_campaign.get('objective', 'N/A')}",
                    "owner": user,
                    "budget": budget,
                    "start_date": start_date,
                    "end_date": end_date,
                    "facebook_synced_at": timezone.now()
                }
            )
            if not created:
                campaign.name = fb_campaign.get("name", campaign.name)
                campaign.budget = budget
                campaign.start_date = start_date
                campaign.end_date = end_date
                campaign.facebook_synced_at = timezone.now()
                campaign.save()
            
            synced_campaigns.append(campaign)
        
        return synced_campaigns
    
    def sync_leads_from_facebook(self, page_id: str, user: User) -> List[Lead]:
        """Sync Facebook Lead Ads as CRM Leads"""
        lead_forms = self.api.get_lead_forms(page_id)
        synced_leads = []
        
        for form in lead_forms:
            leads_data = self.api.get_leads(form["id"])
            
            for lead_data in leads_data:
                # Parse lead data
                field_data = lead_data.get("field_data", [])
                lead_info = {}
                for field in field_data:
                    lead_info[field.get("name", "").lower()] = field.get("values", [""])[0]
                
                # Find or create contact
                contact = None
                if lead_info.get("email") or lead_info.get("full_name"):
                    account = Account.objects.filter(facebook_page_id=page_id).first()
                    if account:
                        first_name = lead_info.get("first_name", lead_info.get("full_name", "").split()[0] if lead_info.get("full_name") else "")
                        last_name = lead_info.get("last_name", " ".join(lead_info.get("full_name", "").split()[1:]) if len(lead_info.get("full_name", "").split()) > 1 else "")
                        
                        contact, _ = Contact.objects.get_or_create(
                            email=lead_info.get("email"),
                            account=account,
                            defaults={
                                "first_name": first_name,
                                "last_name": last_name,
                                "phone": lead_info.get("phone_number", ""),
                                "facebook_user_id": lead_data.get("id", ""),
                                "facebook_synced_at": timezone.now()
                            }
                        )
                
                # Create lead
                created_time = datetime.fromisoformat(lead_data.get("created_time", "").replace("Z", "+00:00")) if lead_data.get("created_time") else timezone.now()
                
                lead, created = Lead.objects.get_or_create(
                    facebook_lead_id=lead_data["id"],
                    defaults={
                        "title": f"Lead from {form.get('name', 'Facebook Form')}",
                        "description": json.dumps(lead_info),
                        "status": "NEW",
                        "owner": user,
                        "contact": contact,
                        "account": account if contact else None,
                        "facebook_lead_form_id": form["id"],
                        "facebook_synced_at": timezone.now(),
                        "created_at": created_time
                    }
                )
                
                synced_leads.append(lead)
        
        return synced_leads
    
    def sync_all(self, user: User) -> Dict[str, Any]:
        """Sync all Facebook data"""
        results = {
            "accounts": [],
            "campaigns": [],
            "leads": []
        }
        
        try:
            # Sync pages as accounts
            pages = self.api.get_pages()
            if pages:
                page = pages[0]  # Use first page
                self.integration.facebook_page_id = page["id"]
                results["accounts"] = self.sync_accounts_from_pages(user)
            
            # Sync ad accounts and campaigns
            ad_accounts = self.api.get_ad_accounts()
            if ad_accounts:
                ad_account = ad_accounts[0]  # Use first ad account
                self.integration.facebook_ad_account_id = ad_account["account_id"]
                results["campaigns"] = self.sync_campaigns_from_facebook(user, ad_account["id"])
            
            # Sync leads
            if self.integration.facebook_page_id:
                results["leads"] = self.sync_leads_from_facebook(self.integration.facebook_page_id, user)
            
            # Update integration
            self.integration.last_synced_at = timezone.now()
            self.integration.save()
            
        except Exception as e:
            print(f"Sync error: {str(e)}")
            raise
        
        return results

