"""
SME - Salesforce Connection Client
OPTIONAL VERSION: Includes option to show system objects
"""
import requests
import time
from typing import Optional, Callable, List
from simple_salesforce import Salesforce
from config.constants import MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT


class SalesforceClient:
    """Manages Salesforce connection and API calls"""
    
    def __init__(self, username: str, password: str, security_token: str, 
                domain: str = 'login', status_callback: Optional[Callable] = None):
        """Initialize Salesforce connection"""
        self.status_callback = status_callback
        self.api_call_count = 0
        
        print(f"Initializing Salesforce connection to {domain}.salesforce.com")
        self._log("Initializing Salesforce Connection...")
        
        try:
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            self.base_url = f"https://{self.sf.sf_instance}"
            self.session_id = self.sf.session_id
            
            # Auto-detect API version
            self.api_version = self._detect_latest_api_version()
            
            self.headers = {
                'Authorization': f'Bearer {self.session_id}',
                'Content-Type': 'application/json'
            }
            
            print(f"✅ Successfully connected to {self.base_url}")
            print(f"✅ Using API version: v{self.api_version}")
            self._log(f"✅ Connected to: {self.base_url}")
            
        except Exception as e:
            print(f"❌ Salesforce connection failed: {str(e)}")
            self._log(f"❌ Connection failed: {str(e)}")
            raise
    
    def _log(self, message: str, verbose: bool = False):
        """Internal logging helper"""
        if self.status_callback:
            self.status_callback(message, verbose=verbose)
    
    def _detect_latest_api_version(self) -> str:
        """Auto-detect the org's latest supported API version"""
        try:
            url = f"{self.base_url}/services/data/"
            response = requests.get(
                url, 
                headers={'Authorization': f'Bearer {self.session_id}'}, 
                timeout=10
            )
            
            if response.status_code == 200:
                versions = response.json()
                if versions and len(versions) > 0:
                    latest = versions[-1]['version']
                    self._log(f"✅ Detected org API version: v{latest}")
                    return latest
        
        except Exception as e:
            self._log(f"⚠️ API version detection failed: {str(e)}")
        
        try:
            sf_version = self.sf.sf_version
            self._log(f"ℹ️ Using simple-salesforce API version: v{sf_version}")
            return sf_version
        except Exception:
            pass
        
        fallback_version = "50.0"
        self._log(f"⚠️ Using minimum safe API version: v{fallback_version}")
        return fallback_version
    
    def fetch_all_objects(self, include_system: bool = False) -> List[str]:
        """
        Fetch all queryable SObjects from the org
        
        Args:
            include_system: If True, includes system/metadata objects (default: False)
        
        Returns:
            List of object API names
        """
        self._log("Fetching all available SObjects from the organization...")
        try:
            response = self.sf.describe()
            
            if include_system:
                # Include ALL queryable objects (including system objects)
                objects = sorted([
                    obj['name'] for obj in response['sobjects'] 
                    if obj.get('queryable', False)
                ])
                self._log(f"✅ Found {len(objects)} queryable objects (including system objects).")
            else:
                # Standard behavior: Exclude system objects
                objects = sorted([
                    obj['name'] for obj in response['sobjects'] 
                    if obj.get('queryable', False) and not obj.get('deprecatedAndHidden', False)
                    and not self._is_system_object(obj['name'])
                ])
                self._log(f"✅ Found {len(objects)} business objects (system objects excluded).")
            
            return objects
        except Exception as e:
            self._log(f"❌ Failed to fetch all SObjects: {str(e)}")
            return []
    
    def _is_system_object(self, object_name: str) -> bool:
        """
        Determine if an object is a system/metadata object
        
        System objects are typically not useful for business data exports
        """
        # Common system object patterns
        system_patterns = [
            'Definition', 'History', 'Share', 'Feed', 'FieldHistory',
            'UserRecordAccess', 'ChangeEvent', 'ViewStat', 'FlexQueue',
            'DandBCompany', 'DatacloudCompany', 'DatacloudDunsNumber',
            'NetworkActivityAudit', 'SetupAuditTrail', 'LoginHistory'
        ]
        
        # Check if object name contains any system patterns
        for pattern in system_patterns:
            if pattern in object_name:
                return True
        
        # Additional specific system objects
        system_objects = {
            'UserLicense', 'UserRole', 'ProfileSkill', 'LoginIp',
            'NetworkMember', 'PermissionSet', 'PermissionSetAssignment'
        }
        
        return object_name in system_objects
    
    def make_api_call(self, url: str, params: dict = None, method: str = "GET") -> Optional[requests.Response]:
        """Make API call with retry logic for rate limits"""
        self.api_call_count += 1
        
        for attempt in range(MAX_RETRIES):
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT)
                else:
                    response = requests.post(url, headers=self.headers, json=params, timeout=REQUEST_TIMEOUT)
                
                # Handle rate limiting
                if response.status_code == 403:
                    error_data = response.json() if response.content else {}
                    error_code = error_data[0].get('errorCode', '') if error_data else ''
                    
                    if error_code == 'REQUEST_LIMIT_EXCEEDED':
                        retry_after = int(response.headers.get('Retry-After', RETRY_DELAY * (attempt + 1)))
                        self._log(f"⚠️ API Rate limit hit. Retrying in {retry_after}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(retry_after)
                        continue
                
                return response
            
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    self._log(f"⚠️ Request timeout. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    self._log(f"❌ Request timeout after {MAX_RETRIES} attempts")
                    return None
            
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    self._log(f"⚠️ API call failed: {str(e)}. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    self._log(f"❌ API call failed after {MAX_RETRIES} attempts: {str(e)}")
                    return None
        
        return None
    
    def describe_object(self, object_name: str):
        """Describe an SObject"""
        return getattr(self.sf, object_name).describe()