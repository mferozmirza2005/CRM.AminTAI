# Facebook Integration Setup Guide

## Overview
This CRM now includes Facebook integration to sync campaigns, leads, accounts, and contacts from Facebook with your CRM.

## Prerequisites
1. Facebook Developer Account
2. Facebook App created in Facebook Developers Console
3. App ID and App Secret from your Facebook App

## Setup Steps

### 1. Create Facebook App
1. Go to https://developers.facebook.com/
2. Click "My Apps" → "Create App"
3. Choose "Business" as the app type
4. Fill in app details and create the app

### 2. Configure Facebook App
1. In your app dashboard, go to "Settings" → "Basic"
2. Note your **App ID** and **App Secret**
3. Add "Facebook Login" product to your app
4. Go to "Facebook Login" → "Settings"
5. Add Valid OAuth Redirect URIs:
   - `http://localhost:8000/api/facebook/callback/` (for development)
   - `https://yourdomain.com/api/facebook/callback/` (for production)

### 3. Request Permissions
Your app needs the following permissions:
- `pages_manage_ads` - Manage Facebook Ad campaigns
- `pages_read_engagement` - Read page engagement data
- `ads_read` - Read ad account information
- `leads_retrieval` - Retrieve lead form data
- `business_management` - Manage business assets

To request these:
1. Go to "App Review" → "Permissions and Features"
2. Request each permission (some may require App Review for production)

### 4. Configure Environment Variables
Add these to your `.env` file:

```env
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
```

### 5. Run Migrations
After setting up the environment variables, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Access Facebook Integration
1. Log in to your CRM
2. Navigate to "Facebook" in the sidebar (for superusers)
3. Click "Connect Facebook Account"
4. Complete OAuth flow
5. Click "Sync Now" to sync your data

## Features

### What Gets Synced

1. **Accounts**: Facebook Pages are synced as CRM Accounts
2. **Campaigns**: Facebook Ad Campaigns are synced as CRM Campaigns
3. **Leads**: Facebook Lead Ads are synced as CRM Leads
4. **Contacts**: Lead form data creates Contacts in CRM

### API Endpoints

- `GET /api/facebook/integrations/oauth_url/` - Get OAuth URL
- `POST /api/facebook/integrations/callback/` - Handle OAuth callback
- `POST /api/facebook/integrations/{id}/sync/` - Sync Facebook data
- `GET /api/facebook/integrations/{id}/pages/` - Get Facebook Pages
- `GET /api/facebook/integrations/{id}/ad_accounts/` - Get Ad Accounts
- `GET /api/facebook/integrations/{id}/campaigns/` - Get Campaigns
- `GET /api/facebook/integrations/{id}/leads/` - Get Leads
- `POST /api/facebook/integrations/{id}/disconnect/` - Disconnect integration

## Troubleshooting

### Common Issues

1. **"Invalid redirect_uri"**
   - Make sure the redirect URI in your Facebook app matches exactly
   - Check that the URL is added in Facebook Login settings

2. **"Insufficient permissions"**
   - Ensure all required permissions are approved
   - Some permissions require App Review for production

3. **"Access token expired"**
   - Reconnect your Facebook account
   - Tokens typically expire after 60 days

4. **"No data synced"**
   - Verify you have Facebook Pages and Ad Accounts
   - Check that you have the necessary permissions
   - Ensure there's actual data (campaigns, leads) to sync

## Security Notes

- Access tokens are stored encrypted in the database
- Tokens expire automatically and need reconnection
- Only authenticated superusers can manage integrations
- All API calls use secure HTTPS endpoints

## Support

For issues or questions, check:
- Facebook Graph API Documentation: https://developers.facebook.com/docs/graph-api
- Facebook Marketing API: https://developers.facebook.com/docs/marketing-apis

