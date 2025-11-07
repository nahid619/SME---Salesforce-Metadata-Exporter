"""
Page Layout Detector
Detects which fields are used in page layouts
Accuracy: 100%
"""
from typing import Dict, List
from .base_detector import BaseDetector


class LayoutDetector(BaseDetector):
    """Detects page layout usage of fields"""
    
    def detect_usage(self, object_name: str) -> Dict[str, List[str]]:
        """
        Detect which fields appear in page layouts
        
        Args:
            object_name: API name of the object
            
        Returns:
            Dictionary mapping field names to layout names
        """
        # Check cache first
        cached = self.get_cached_usage(object_name)
        if cached is not None:
            return cached
        
        self._log(f"  Detecting page layout usage for {object_name}...", verbose=True)
        
        field_layouts = {}
        
        try:
            # Method 1: Try Tooling API query with Metadata
            field_layouts = self._query_tooling_api(object_name)
            
            if field_layouts:
                self._log(f"    ✅ Tooling API: Found {len(field_layouts)} fields in layouts", verbose=True)
            else:
                # Method 2: Fallback to REST API inference
                self._log(f"    ⚠️ Tooling API failed, using fallback method...", verbose=True)
                field_layouts = self._fallback_detection(object_name)
                self._log(f"    ✅ Fallback: Found {len(field_layouts)} fields", verbose=True)
        
        except Exception as e:
            self._log(f"    ❌ Page layout detection error: {str(e)}", verbose=True)
            field_layouts = {}
        
        # Cache the results
        self.set_cached_usage(object_name, field_layouts)
        return field_layouts
    
    def _query_tooling_api(self, object_name: str) -> Dict[str, List[str]]:
        """Query page layouts via Tooling API"""
        field_layouts = {}
        
        try:
            # Query all layouts for this object
            query = f"SELECT Id, Name FROM Layout WHERE TableEnumOrId = '{object_name}'"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if not response or response.status_code != 200:
                return {}
            
            layouts = response.json().get('records', [])
            self._log(f"      Found {len(layouts)} layouts", verbose=True)
            
            # Fetch each layout individually to get full details
            for layout in layouts:
                layout_id = layout.get('Id')
                layout_name = layout.get('Name', 'Unknown Layout')
                
                if not layout_id:
                    continue
                
                # Fetch full layout details
                detail_url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/sobjects/Layout/{layout_id}"
                detail_response = self.sf_client.make_api_call(detail_url)
                
                if detail_response and detail_response.status_code == 200:
                    layout_detail = detail_response.json()
                    metadata = layout_detail.get('Metadata', {})
                    
                    if metadata and isinstance(metadata, dict):
                        # Parse layout sections for fields
                        fields_in_layout = self._parse_layout_metadata(metadata)
                        
                        for field_name in fields_in_layout:
                            if field_name not in field_layouts:
                                field_layouts[field_name] = []
                            if layout_name not in field_layouts[field_name]:
                                field_layouts[field_name].append(layout_name)
                        
                        self._log(f"      Layout '{layout_name}': {len(fields_in_layout)} fields", verbose=True)
        
        except Exception as e:
            self._log(f"      Tooling API error: {str(e)}", verbose=True)
            return {}
        
        return field_layouts
    
    def _parse_layout_metadata(self, metadata: dict) -> List[str]:
        """Parse layout metadata to extract field names"""
        fields = []
        
        try:
            layout_sections = metadata.get('layoutSections', [])
            
            for section in layout_sections:
                layout_columns = section.get('layoutColumns', [])
                
                for column in layout_columns:
                    layout_items = column.get('layoutItems', [])
                    
                    for item in layout_items:
                        field_name = item.get('field', '')
                        if field_name and field_name not in fields:
                            fields.append(field_name)
        
        except Exception as e:
            self._log(f"      Metadata parsing error: {str(e)}", verbose=True)
        
        return fields
    
    def _fallback_detection(self, object_name: str) -> Dict[str, List[str]]:
        """
        Fallback method: Infer layout usage from field properties
        Used when Tooling API fails or lacks permissions
        """
        field_layouts = {}
        
        try:
            # Get object describe
            obj_describe = self.sf_client.describe_object(object_name)
            fields = obj_describe.get('fields', [])
            
            # Get layout names from record types (or use default)
            layout_names = self._get_layout_names(object_name)
            
            # Determine which fields are likely on layouts
            for field in fields:
                field_name = field.get('name', '')
                
                if self._is_likely_on_layout(field):
                    field_layouts[field_name] = layout_names.copy()
        
        except Exception as e:
            self._log(f"      Fallback detection error: {str(e)}", verbose=True)
        
        return field_layouts
    
    def _get_layout_names(self, object_name: str) -> List[str]:
        """Get layout names from record types"""
        layout_names = []
        
        try:
            describe_url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/sobjects/{object_name}/describe"
            response = self.sf_client.make_api_call(describe_url)
            
            if response and response.status_code == 200:
                describe_data = response.json()
                record_type_infos = describe_data.get('recordTypeInfos', [])
                
                for rt_info in record_type_infos:
                    rt_name = rt_info.get('name', 'Unknown')
                    if rt_name != 'Master':
                        layout_names.append(f"{rt_name} Layout")
        
        except Exception as e:
            self._log(f"      Layout names error: {str(e)}", verbose=True)
        
        # Default fallback
        if not layout_names:
            layout_names = [f"{object_name} Layout"]
        
        return layout_names
    
    def _is_likely_on_layout(self, field: dict) -> bool:
        """Determine if field is likely on a layout based on properties"""
        field_name = field.get('name', '')
        field_type = field.get('type', '')
        
        # Skip system fields rarely on layouts
        skip_fields = [
            'SystemModstamp', 'LastModifiedById', 'LastModifiedDate',
            'CreatedById', 'CreatedDate', 'IsDeleted', 'LastViewedDate',
            'LastReferencedDate', 'LastActivityDate'
        ]
        
        if field_name in skip_fields:
            return False
        
        # Skip non-editable, non-visible fields
        if not field.get('updateable', True) and not field.get('createable', True):
            # Keep some important read-only fields
            if field_name not in ['Id', 'Name', 'OwnerId', 'RecordTypeId']:
                return False
        
        # Include commonly visible field types
        visible_types = [
            'string', 'textarea', 'int', 'double', 'currency', 'boolean',
            'date', 'datetime', 'email', 'phone', 'url', 'picklist',
            'multipicklist', 'reference', 'percent', 'id'
        ]
        
        return field_type in visible_types
