from pydantic import BaseModel

SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "secret", "api_key"}

def clean_sensitive(obj):
    if obj is None:
        return None
    if isinstance(obj, BaseModel):
        obj = obj.model_dump(exclude_unset=True)
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            if k.lower() in SENSITIVE_KEYS:
                clean[k] = "***"
            else:
                clean[k] = clean_sensitive(v)
        return clean
    if isinstance(obj, list):
        return [clean_sensitive(x) for x in obj]
    return obj