from .models import CRMSettings

def crm_settings(request):
    settings_obj, _ = CRMSettings.objects.get_or_create(id=1)
    return {"crm_settings": settings_obj}
