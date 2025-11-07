"""
Code Search Detector
Searches for field references in Apex Classes, Visualforce Pages, and Triggers
Accuracy: 90-95% (text-based search, may have false positives)
"""
from typing import Dict, List, Set
import re
from .base_detector import BaseDetector


class CodeSearchDetector(BaseDetector):
    """Searches code for field references"""
    
    def __init__(self, sf_client, log_callback=None):
        super().__init__(sf_client, log_callback)
        self.apex_cache = None
        self.vf_cache = None
        self.trigger_cache = None
    
    def detect_usage(self, object_name: str, field_names: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """
        Search code for field references
        
        Args:
            object_name: API name of the object
            field_names: List of field API names to search for
            
        Returns:
            Dictionary with structure:
            {
                'apex_classes': {field_name: [class_names]},
                'visualforce': {field_name: [page_names]},
                'triggers': {field_name: [trigger_names]}
            }
        """
        self._log(f"  Searching code for field references in {object_name}...", verbose=True)
        
        results = {
            'apex_classes': {},
            'visualforce': {},
            'triggers': {}
        }
        
        # Load code once for all fields (optimization)
        if self.apex_cache is None:
            self.apex_cache = self._load_apex_classes()
        if self.vf_cache is None:
            self.vf_cache = self._load_visualforce_pages()
        if self.trigger_cache is None:
            self.trigger_cache = self._load_triggers(object_name)
        
        # Search for each field
        for field_name in field_names:
            # Search Apex Classes
            apex_matches = self._search_in_code(field_name, self.apex_cache)
            if apex_matches:
                results['apex_classes'][field_name] = apex_matches
            
            # Search Visualforce Pages
            vf_matches = self._search_in_code(field_name, self.vf_cache)
            if vf_matches:
                results['visualforce'][field_name] = vf_matches
            
            # Search Triggers
            trigger_matches = self._search_in_code(field_name, self.trigger_cache)
            if trigger_matches:
                results['triggers'][field_name] = trigger_matches
        
        total_apex = len(results['apex_classes'])
        total_vf = len(results['visualforce'])
        total_triggers = len(results['triggers'])
        
        self._log(f"    ✅ Code search complete: {total_apex} in Apex, {total_vf} in VF, {total_triggers} in Triggers", verbose=True)
        
        return results
    
    def _load_apex_classes(self) -> Dict[str, str]:
        """
        Load all Apex class bodies
        Returns dict: {class_name: body}
        """
        apex_classes = {}
        
        try:
            self._log(f"    Loading Apex classes...", verbose=True)
            
            # Query Apex classes (limit to reduce API load)
            query = "SELECT Name, Body FROM ApexClass WHERE Status = 'Active' LIMIT 500"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                classes = response.json().get('records', [])
                
                for cls in classes:
                    name = cls.get('Name', '')
                    body = cls.get('Body', '')
                    if name and body:
                        apex_classes[name] = body
                
                self._log(f"      Loaded {len(apex_classes)} Apex classes", verbose=True)
        
        except Exception as e:
            self._log(f"      ⚠️ Apex class loading error: {str(e)}", verbose=True)
        
        return apex_classes
    
    def _load_visualforce_pages(self) -> Dict[str, str]:
        """
        Load all Visualforce page markup
        Returns dict: {page_name: markup}
        """
        vf_pages = {}
        
        try:
            self._log(f"    Loading Visualforce pages...", verbose=True)
            
            # Query VF pages (limit to reduce API load)
            query = "SELECT Name, Markup FROM ApexPage LIMIT 500"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                pages = response.json().get('records', [])
                
                for page in pages:
                    name = page.get('Name', '')
                    markup = page.get('Markup', '')
                    if name and markup:
                        vf_pages[name] = markup
                
                self._log(f"      Loaded {len(vf_pages)} Visualforce pages", verbose=True)
        
        except Exception as e:
            self._log(f"      ⚠️ Visualforce loading error: {str(e)}", verbose=True)
        
        return vf_pages
    
    def _load_triggers(self, object_name: str) -> Dict[str, str]:
        """
        Load triggers for specific object
        Returns dict: {trigger_name: body}
        """
        triggers = {}
        
        try:
            self._log(f"    Loading triggers for {object_name}...", verbose=True)
            
            # Query triggers for this object
            query = f"SELECT Name, Body FROM ApexTrigger WHERE TableEnumOrId = '{object_name}' AND Status = 'Active'"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                trigger_records = response.json().get('records', [])
                
                for trigger in trigger_records:
                    name = trigger.get('Name', '')
                    body = trigger.get('Body', '')
                    if name and body:
                        triggers[name] = body
                
                self._log(f"      Loaded {len(triggers)} triggers", verbose=True)
        
        except Exception as e:
            self._log(f"      ⚠️ Trigger loading error: {str(e)}", verbose=True)
        
        return triggers
    
    def _search_in_code(self, field_name: str, code_dict: Dict[str, str]) -> List[str]:
        """
        Search for field name in code
        
        Args:
            field_name: Field API name to search for
            code_dict: Dictionary of {name: code_body}
            
        Returns:
            List of code component names where field was found
        """
        matches = []
        
        # Create search patterns
        patterns = [
            rf'\b{re.escape(field_name)}\b',  # Exact field name
            rf'\.{re.escape(field_name)}\b',  # Object.FieldName
            rf'\["{re.escape(field_name)}"\]',  # Map access ['FieldName']
            rf"\['{re.escape(field_name)}'\]",  # Map access ['FieldName']
        ]
        
        for name, code in code_dict.items():
            if not code:
                continue
            
            # Check if field appears in code
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    if name not in matches:
                        matches.append(name)
                    break
        
        return matches
    
    def clear_code_cache(self):
        """Clear all cached code to free memory"""
        self.apex_cache = None
        self.vf_cache = None
        self.trigger_cache = None
        self.clear_cache()
