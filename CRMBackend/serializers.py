from .models import User, Account, Contact, Lead, Deal, Campaign, Task, CRMSettings, FacebookIntegration
from django.contrib.auth.password_validation import validate_password
from django.db import connection
from rest_framework import serializers

def _has_facebook_columns(table_name, column_name):
    """Check if a specific Facebook column exists in database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND column_name = %s
            """, [table_name, column_name])
            return cursor.fetchone() is not None
    except:
        return False

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','email','first_name','last_name','role','region','is_active')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.EMPLOYEE)

    class Meta:
        model = User
        fields = ('email','password','first_name','last_name','role','region')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class CRMSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRMSettings
        fields = "__all__"

# Minimal serializers for CRM models
class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically exclude Facebook fields if they don't exist in DB
        if not _has_facebook_columns('CRMBackend_account', 'facebook_page_id'):
            self.fields.pop('facebook_page_id', None)
            self.fields.pop('facebook_synced_at', None)

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not _has_facebook_columns('CRMBackend_contact', 'facebook_user_id'):
            self.fields.pop('facebook_user_id', None)
            self.fields.pop('facebook_synced_at', None)

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not _has_facebook_columns('CRMBackend_lead', 'facebook_lead_id'):
            self.fields.pop('facebook_lead_id', None)
            self.fields.pop('facebook_lead_form_id', None)
            self.fields.pop('facebook_synced_at', None)

class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not _has_facebook_columns('CRMBackend_deal', 'facebook_event_id'):
            self.fields.pop('facebook_event_id', None)
            self.fields.pop('facebook_synced_at', None)

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not _has_facebook_columns('CRMBackend_campaign', 'facebook_campaign_id'):
            self.fields.pop('facebook_campaign_id', None)
            self.fields.pop('facebook_ad_set_id', None)
            self.fields.pop('facebook_synced_at', None)

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class FacebookIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacebookIntegration
        fields = ('id', 'facebook_user_id', 'facebook_page_id', 'facebook_ad_account_id', 
                  'is_active', 'last_synced_at', 'created_at')
        read_only_fields = ('id', 'created_at', 'last_synced_at')
