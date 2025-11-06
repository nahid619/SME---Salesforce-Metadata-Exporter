"""
SME - Metadata Exporter Module (UPDATED - Matches Required Format)
Exports field metadata matching the exact format from Opportunity Object Fields Definition
"""
import threading
from typing import List, Dict, Optional, Tuple, Callable
from core.salesforce_client import SalesforceClient
from utils.file_handler import FileHandler


class FieldMetadata:
    """Represents field metadata matching required format"""
    def __init__(self):
        self.object_name = ""
        self.field_label = ""
        self.api_name = ""
        self.data_type = ""
        self.length = ""
        self.field_type = ""  # Standard/Custom
        self.required = ""
        self.formula = ""
        self.help_text = ""
        self.field_usage = ""  # Multi-line usage information


class MetadataExporter:
    """Handles metadata extraction and export"""
    
    def __init__(self, sf_client: SalesforceClient, status_callback: Optional[Callable] = None):
        """
        Initialize metadata exporter
        
        Args:
            sf_client: Salesforce client instance
            status_callback: Optional callback for status updates
        """
        self.sf_client = sf_client
        self.status_callback = status_callback
        self.cancel_event = threading.Event()
        self.file_handler = FileHandler(log_callback=self._log_status)
    
    def _log_status(self, message: str, verbose: bool = False):
        """Internal logging helper"""
        if self.status_callback:
            self.status_callback(message, verbose=verbose)
    
    def cancel_export(self):
        """Signal cancellation of the export"""
        self.cancel_event.set()
        self._log_status("🛑 Cancel requested by user...")
    
    def export_metadata(self, object_names: List[str], output_path: str,
                       export_format: str = "excel",
                       include_usage: bool = False,
                       custom_only: bool = False,
                       progress_callback: Optional[Callable] = None) -> Tuple[str, Dict]:
        """
        Export field metadata for specified objects
        
        Args:
            object_names: List of object API names
            output_path: Path to save the output file
            export_format: 'excel' or 'csv'
            include_usage: Whether to include field usage analysis
            custom_only: Export only custom fields
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (output_path, statistics_dict)
        """
        self.cancel_event.clear()
        self.sf_client.api_call_count = 0
        
        self._log_status("=" * 70)
        self._log_status("=== Starting Metadata Export ===")
        self._log_status("=" * 70)
        self._log_status(f"Total objects to process: {len(object_names)}")
        self._log_status(f"Using API version: v{self.sf_client.api_version}")
        self._log_status(f"Export format: {export_format.upper()}")
        self._log_status(f"Custom fields only: {'Yes' if custom_only else 'No'}")
        self._log_status(f"Include usage analysis: {'Yes' if include_usage else 'No'}")
        self._log_status("")
        
        stats = {
            'total_objects': len(object_names),
            'successful_objects': 0,
            'failed_objects': 0,
            'objects_not_found': 0,
            'total_fields': 0,
            'standard_fields': 0,
            'custom_fields': 0,
            'formula_fields': 0,
            'lookup_fields': 0,
            'picklist_fields': 0,
            'failed_object_details': [],
            'objects_not_found_list': [],
            'cancelled': False,
            'api_calls_made': 0
        }
        
        # PRE-SCAN: Get field counts for accurate progress tracking
        self._log_status("Pre-scanning objects to calculate progress...")
        object_field_counts = {}
        total_fields_to_process = 0
        
        for obj_name in object_names:
            if self.cancel_event.is_set():
                break
            try:
                obj_describe = self.sf_client.describe_object(obj_name)
                fields = obj_describe['fields']
                
                # Apply custom_only filter to count
                if custom_only:
                    field_count = sum(1 for f in fields if f['name'].endswith('__c'))
                else:
                    field_count = len(fields)
                
                object_field_counts[obj_name] = field_count
                total_fields_to_process += field_count
            except Exception as e:
                # If pre-scan fails, estimate 50 fields per object
                object_field_counts[obj_name] = 50
                total_fields_to_process += 50
        
        if total_fields_to_process > 0:
            self._log_status(f"✅ Found {total_fields_to_process} total fields across {len(object_names)} objects")
            self._log_status("")
        
        # Storage for all metadata by object
        all_metadata: Dict[str, List[FieldMetadata]] = {}
        
        # Get usage metadata if enabled
        usage_cache = {}
        if include_usage:
            self._log_status("Pre-loading usage metadata for all objects...")
            usage_cache = self._get_comprehensive_usage_cache(object_names)
        
        # Track fields processed for progress
        fields_processed = 0
        
        # Process each object
        for i, obj_name in enumerate(object_names, 1):
            if self.cancel_event.is_set():
                self._log_status("🛑 Export cancelled by user")
                self._log_status("")
                stats['cancelled'] = True
                break
            
            expected_fields = object_field_counts.get(obj_name, 0)
            self._log_status(f"[{i}/{len(object_names)}] Processing object: {obj_name} ({expected_fields} fields)")
            
            try:
                field_metadata_list = self._process_object_metadata(
                    obj_name, 
                    custom_only, 
                    include_usage,
                    usage_cache.get(obj_name, {})
                )
                
                if field_metadata_list is None:
                    # Object not found
                    stats['objects_not_found'] += 1
                    stats['objects_not_found_list'].append(obj_name)
                    stats['failed_object_details'].append({
                        'name': obj_name, 
                        'reason': 'Object does not exist in org'
                    })
                    self._log_status(f"  ⚠️  Object not found in org")
                    # Still count expected fields for progress
                    fields_processed += expected_fields
                elif len(field_metadata_list) == 0:
                    self._log_status(f"  ℹ️  No fields found (custom_only filter applied)")
                    stats['successful_objects'] += 1
                    fields_processed += expected_fields
                else:
                    all_metadata[obj_name] = field_metadata_list
                    stats['successful_objects'] += 1
                    stats['total_fields'] += len(field_metadata_list)
                    
                    # Update fields processed
                    fields_processed += len(field_metadata_list)
                    
                    # Count field types
                    for field in field_metadata_list:
                        if field.field_type == "Custom":
                            stats['custom_fields'] += 1
                        else:
                            stats['standard_fields'] += 1
                        
                        if field.formula:
                            stats['formula_fields'] += 1
                        if "Lookup" in field.data_type:
                            stats['lookup_fields'] += 1
                        if "Picklist" in field.data_type:
                            stats['picklist_fields'] += 1
                    
                    self._log_status(f"  ✅ Extracted {len(field_metadata_list)} fields")
                
                # Update progress based on fields processed
                if progress_callback and total_fields_to_process > 0:
                    progress_callback(fields_processed, total_fields_to_process)
            
            except Exception as e:
                error_msg = str(e)
                self._log_status(f"  ❌ ERROR: {error_msg}")
                stats['failed_objects'] += 1
                stats['failed_object_details'].append({'name': obj_name, 'reason': error_msg})
                # Still count expected fields for progress
                fields_processed += expected_fields
                if progress_callback and total_fields_to_process > 0:
                    progress_callback(fields_processed, total_fields_to_process)
            
            self._log_status("")
        
        if self.cancel_event.is_set():
            self._log_status("🛑 Export was cancelled. Partial data will be saved.")
            self._log_status("")
        
        stats['api_calls_made'] = self.sf_client.api_call_count
        
        # Create output file
        self._log_status("=" * 70)
        self._log_status("=== Creating Output File ===")
        self._log_status(f"Total API calls made: {self.sf_client.api_call_count}")
        
        if export_format == "csv":
            final_output_path = self._create_csv_output(all_metadata, output_path)
        else:
            final_output_path = self._create_excel_output(all_metadata, output_path)
        
        return final_output_path, stats
    
    def _process_object_metadata(self, object_name: str, custom_only: bool, 
                                 include_usage: bool,
                                 usage_data: Dict) -> Optional[List[FieldMetadata]]:
        """
        Process metadata for a single object
        
        Returns:
            List of FieldMetadata, or None if object doesn't exist
        """
        if self.cancel_event.is_set():
            return []
        
        try:
            obj_describe = self.sf_client.describe_object(object_name)
        except Exception as e:
            if 'NOT_FOUND' in str(e) or 'INVALID_TYPE' in str(e):
                return None
            raise
        
        field_metadata_list = []
        
        for field in obj_describe['fields']:
            # Skip if custom_only and this is standard field
            if custom_only and not field['name'].endswith('__c'):
                continue
            
            metadata = FieldMetadata()
            
            # Column 1: Object - Populate with object name
            metadata.object_name = object_name
            
            # Column 2: Field Label
            metadata.field_label = field.get('label', '')
            
            # Column 3: API Name
            metadata.api_name = field.get('name', '')
            
            # Column 4: Data Type (formatted like the example)
            metadata.data_type = self._format_data_type(field)
            
            # Column 5: Length
            if field.get('length'):
                metadata.length = str(field['length'])
            elif field.get('byteLength'):
                metadata.length = str(field['byteLength'])
            else:
                metadata.length = ""
            
            # Column 6: Field Type
            metadata.field_type = "Custom" if field['name'].endswith('__c') else "Standard"
            
            # Column 7: Required
            if not field.get('nillable', True) or field.get('defaultedOnCreate', False):
                metadata.required = "Required"
            else:
                metadata.required = ""
            
            # Column 8: Formula
            if field.get('calculatedFormula'):
                metadata.formula = field['calculatedFormula']
            else:
                metadata.formula = ""
            
            # Column 9: Help Text
            if field.get('inlineHelpText'):
                metadata.help_text = field['inlineHelpText']
            else:
                metadata.help_text = ""
            
            # Column 10: Field Usage (comprehensive)
            if include_usage:
                metadata.field_usage = self._build_field_usage(
                    field['name'], 
                    usage_data
                )
            else:
                metadata.field_usage = ""
            
            field_metadata_list.append(metadata)
        
        return field_metadata_list
    
    def _format_data_type(self, field: Dict) -> str:
        """
        Format data type to match required format
        Examples: 
        - "Lookup (Account)"
        - "Number (16, 2)"
        - "Text"
        - "Picklist (Multi-Select)"
        """
        field_type = field.get('type', '')
        
        # Handle reference (Lookup/Master-Detail)
        if field_type == 'reference':
            ref_objects = field.get('referenceTo', [])
            if ref_objects:
                ref_str = ', '.join(ref_objects)
                return f"Lookup ({ref_str})"
            return "Lookup"
        
        # Handle numeric types with precision/scale
        if field_type in ['double', 'currency', 'percent']:
            precision = field.get('precision', '')
            scale = field.get('scale', '')
            if precision and scale:
                type_name = field_type.title()
                if field_type == 'double':
                    type_name = "Number"
                return f"{type_name} ({precision}, {scale})"
        
        if field_type == 'int':
            precision = field.get('precision', 0)
            return f"Integer ({precision}, 0)"
        
        # Handle picklist types
        if field_type == 'picklist':
            return "Picklist"
        
        if field_type == 'multipicklist':
            return "Picklist (Multi-Select)"
        
        # Handle text types
        if field_type == 'string':
            return "Text"
        
        if field_type == 'textarea':
            return "Long Text Area"
        
        # Handle date/time types
        if field_type == 'datetime':
            return "Date/Time"
        
        if field_type == 'date':
            return "Date"
        
        if field_type == 'time':
            return "Time"
        
        # Handle boolean
        if field_type == 'boolean':
            return "Checkbox"
        
        # Handle email, phone, url
        if field_type == 'email':
            return "Email"
        
        if field_type == 'phone':
            return "Phone"
        
        if field_type == 'url':
            return "URL"
        
        # Handle ID
        if field_type == 'id':
            return "id"
        
        # Default: return type as-is with first letter capitalized
        return field_type.title() if field_type else ""
    
    def _get_comprehensive_usage_cache(self, object_names: List[str]) -> Dict[str, Dict]:
        """
        Get comprehensive usage data for all objects
        Returns dict: {object_name: {field_name: usage_data}}
        """
        cache = {}
        
        for obj_name in object_names:
            if self.cancel_event.is_set():
                break
            
            cache[obj_name] = {
                'page_layouts': self._get_page_layout_usage(obj_name),
                'validation_rules': self._get_validation_rules(obj_name),
                'workflows': self._get_workflow_rules(obj_name),
                'apex_classes': self._get_apex_usage(obj_name),
                'vf_components': self._get_vf_usage(obj_name)
            }
        
        return cache
    
    def _get_page_layout_usage(self, object_name: str) -> Dict[str, List[str]]:
        """Get page layouts where each field is used"""
        field_layouts = {}
        
        try:
            query = f"SELECT Id, Name, Metadata FROM Layout WHERE TableEnumOrId = '{object_name}'"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                layouts = response.json().get('records', [])
                
                self._log_status(f"  Found {len(layouts)} page layouts for {object_name}", verbose=True)
                
                for layout in layouts:
                    layout_name = layout.get('Name', '')
                    metadata = layout.get('Metadata', {})
                    
                    if not metadata:
                        self._log_status(f"    No metadata for layout: {layout_name}", verbose=True)
                        continue
                    
                    # Parse layout sections for fields
                    layout_sections = metadata.get('layoutSections', [])
                    self._log_status(f"    Layout '{layout_name}' has {len(layout_sections)} sections", verbose=True)
                    
                    for section in layout_sections:
                        layout_columns = section.get('layoutColumns', [])
                        for column in layout_columns:
                            layout_items = column.get('layoutItems', [])
                            for item in layout_items:
                                field_name = item.get('field', '')
                                if field_name:
                                    if field_name not in field_layouts:
                                        field_layouts[field_name] = []
                                    if layout_name not in field_layouts[field_name]:
                                        field_layouts[field_name].append(layout_name)
                                        self._log_status(f"      Found field '{field_name}' in layout '{layout_name}'", verbose=True)
                
                self._log_status(f"  Total fields mapped: {len(field_layouts)}", verbose=True)
        
        except Exception as e:
            self._log_status(f"  Warning: Could not load page layouts for {object_name}: {str(e)}")
        
        return field_layouts
    
    def _get_validation_rules(self, object_name: str) -> Dict[str, List[str]]:
        """Get validation rules that reference each field"""
        field_validations = {}
        
        try:
            query = f"SELECT ValidationName, ErrorConditionFormula FROM ValidationRule WHERE EntityDefinition.QualifiedApiName = '{object_name}' AND Active = true"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                rules = response.json().get('records', [])
                
                self._log_status(f"  Found {len(rules)} validation rules for {object_name}", verbose=True)
                
                for rule in rules:
                    rule_name = rule.get('ValidationName', '')
                    formula = rule.get('ErrorConditionFormula', '')
                    
                    if formula:
                        self._log_status(f"    Checking rule '{rule_name}'", verbose=True)
                        # Extract potential field names from formula
                        # Look for patterns like: FieldName, FieldName__c
                        import re
                        # Match field names (alphanumeric + underscores, possibly ending with __c)
                        field_pattern = r'\b([A-Z][a-zA-Z0-9_]*(?:__c)?)\b'
                        potential_fields = re.findall(field_pattern, formula)
                        
                        for field in potential_fields:
                            # Skip formula functions and keywords
                            if field.upper() not in ['IF', 'AND', 'OR', 'NOT', 'ISBLANK', 'ISNULL', 'TEXT', 'VALUE', 'TODAY', 'NOW', 'TRUE', 'FALSE']:
                                if field not in field_validations:
                                    field_validations[field] = []
                                if rule_name not in field_validations[field]:
                                    field_validations[field].append(rule_name)
                                    self._log_status(f"      Field '{field}' found in rule", verbose=True)
                
                self._log_status(f"  Total fields in validation rules: {len(field_validations)}", verbose=True)
        
        except Exception as e:
            self._log_status(f"  Warning: Could not load validation rules for {object_name}: {str(e)}")
        
        return field_validations
    
    def _get_workflow_rules(self, object_name: str) -> Dict[str, List[str]]:
        """Get workflow rules that reference each field"""
        field_workflows = {}
        
        try:
            query = f"SELECT Name, Formula FROM WorkflowRule WHERE TableEnumOrId = '{object_name}'"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                rules = response.json().get('records', [])
                
                self._log_status(f"  Found {len(rules)} workflows for {object_name}", verbose=True)
                
                for rule in rules:
                    rule_name = rule.get('Name', '')
                    formula = rule.get('Formula', '')
                    
                    if formula:
                        self._log_status(f"    Checking workflow '{rule_name}'", verbose=True)
                        # Extract potential field names from formula
                        import re
                        field_pattern = r'\b([A-Z][a-zA-Z0-9_]*(?:__c)?)\b'
                        potential_fields = re.findall(field_pattern, formula)
                        
                        for field in potential_fields:
                            # Skip formula functions and keywords
                            if field.upper() not in ['IF', 'AND', 'OR', 'NOT', 'ISBLANK', 'ISNULL', 'TEXT', 'VALUE', 'TODAY', 'NOW', 'TRUE', 'FALSE']:
                                if field not in field_workflows:
                                    field_workflows[field] = []
                                if rule_name not in field_workflows[field]:
                                    field_workflows[field].append(rule_name)
                                    self._log_status(f"      Field '{field}' found in workflow", verbose=True)
                
                self._log_status(f"  Total fields in workflows: {len(field_workflows)}", verbose=True)
        
        except Exception as e:
            self._log_status(f"  Warning: Could not load workflows for {object_name}: {str(e)}")
        
        return field_workflows
    
    def _get_apex_usage(self, object_name: str) -> Dict[str, List[str]]:
        """Get Apex classes that reference each field (basic implementation)"""
        # Note: Full Apex parsing would require complex code analysis
        # This is a placeholder that could be enhanced
        return {}
    
    def _get_vf_usage(self, object_name: str) -> Dict[str, List[str]]:
        """Get Visualforce components that reference each field (basic implementation)"""
        # Note: Full VF parsing would require complex markup analysis
        # This is a placeholder that could be enhanced
        return {}
    
    def _build_field_usage(self, field_name: str, usage_data: Dict) -> str:
        """
        Build comprehensive field usage string matching required format
        
        Format:
        Page Layouts
        - Layout 1
        - Layout 2
        
        Validation Rules
        - Rule 1
        
        Workflows
        - Workflow 1
        
        Apex Classes
        - Class1
        - Class2
        
        VisualForce Components
        - Component1
        """
        usage_lines = []
        
        self._log_status(f"      Building usage for field: {field_name}", verbose=True)
        
        # Page Layouts
        page_layouts = usage_data.get('page_layouts', {}).get(field_name, [])
        self._log_status(f"        Page layouts found: {len(page_layouts)}", verbose=True)
        if page_layouts:
            usage_lines.append("Page Layouts")
            for layout in sorted(page_layouts):
                usage_lines.append(f"- {layout}")
            usage_lines.append("")  # Empty line after section
        
        # Validation Rules
        validations = usage_data.get('validation_rules', {}).get(field_name, [])
        self._log_status(f"        Validation rules found: {len(validations)}", verbose=True)
        if validations:
            usage_lines.append("Validation Rules")
            for rule in sorted(validations):
                usage_lines.append(f"- {rule}")
            usage_lines.append("")
        
        # Workflows
        workflows = usage_data.get('workflows', {}).get(field_name, [])
        self._log_status(f"        Workflows found: {len(workflows)}", verbose=True)
        if workflows:
            usage_lines.append("Workflows")
            for wf in sorted(workflows):
                usage_lines.append(f"- {wf}")
            usage_lines.append("")
        
        # Apex Classes
        apex_classes = usage_data.get('apex_classes', {}).get(field_name, [])
        if apex_classes:
            usage_lines.append("Apex Classes")
            for cls in sorted(apex_classes):
                usage_lines.append(f"- {cls}")
            usage_lines.append("")
        
        # VisualForce Components
        vf_components = usage_data.get('vf_components', {}).get(field_name, [])
        if vf_components:
            usage_lines.append("VisualForce Components")
            for vf in sorted(vf_components):
                usage_lines.append(f"- {vf}")
            usage_lines.append("")
        
        # Remove trailing empty line
        if usage_lines and usage_lines[-1] == "":
            usage_lines.pop()
        
        result = "\n".join(usage_lines)
        if result:
            self._log_status(f"        Usage result: {len(result)} characters", verbose=True)
        else:
            self._log_status(f"        No usage data found for {field_name}", verbose=True)
        
        return result
    
    def _create_excel_output(self, all_metadata: Dict[str, List[FieldMetadata]], output_path: str) -> str:
        """Create Excel file with one sheet per object"""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
        
        wb = Workbook()
        
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            del wb['Sheet']
        
        # Header row matching required format
        headers = [
            'Object ', 'Field Label', 'API Name', 'Data Type', 'Length',
            'Field Type', 'Required', 'Formula', 'Help Text', 'Field Usage'
        ]
        
        # Create sheet for each object
        for obj_name in sorted(all_metadata.keys()):
            if self.cancel_event.is_set():
                break
            
            fields = all_metadata[obj_name]
            
            # Create sheet (truncate name if too long)
            sheet_name = obj_name[:31] if len(obj_name) > 31 else obj_name
            ws = wb.create_sheet(sheet_name)
            
            # Write header
            ws.append(headers)
            
            # Format header
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Write data
            for field in fields:
                row = [
                    field.object_name,
                    field.field_label,
                    field.api_name,
                    field.data_type,
                    field.length,
                    field.field_type,
                    field.required,
                    field.formula,
                    field.help_text,
                    field.field_usage
                ]
                ws.append(row)
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    try:
                        if cell.value:
                            # For multi-line cells, use max line length
                            cell_value = str(cell.value)
                            if '\n' in cell_value:
                                max_length = max(max_length, max(len(line) for line in cell_value.split('\n')))
                            else:
                                max_length = max(max_length, len(cell_value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 80)  # Increased max width for usage column
                ws.column_dimensions[col_letter].width = adjusted_width
            
            # Set text wrapping for all cells (important for multi-line usage)
            for row in ws.iter_rows():
                for cell in row:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
            
            # Freeze header row
            ws.freeze_panes = "A2"
            
            self._log_status(f"  Created sheet: {sheet_name} ({len(fields)} fields)")
        
        wb.save(output_path)
        self._log_status(f"✅ Excel file created: {output_path}")
        self._log_status(f"✅ Total sheets: {len(wb.worksheets)}")
        self._log_status(f"✅ Total fields exported: {sum(len(fields) for fields in all_metadata.values())}")
        self._log_status("=" * 70)
        
        return output_path
    
    def _create_csv_output(self, all_metadata: Dict[str, List[FieldMetadata]], output_path: str) -> str:
        """Create CSV file with all objects"""
        import csv
        
        headers = [
            'Object ', 'Field Label', 'API Name', 'Data Type', 'Length',
            'Field Type', 'Required', 'Formula', 'Help Text', 'Field Usage'
        ]
        
        # Collect all rows
        all_rows = [headers]
        
        for obj_name in sorted(all_metadata.keys()):
            if self.cancel_event.is_set():
                break
            
            for field in all_metadata[obj_name]:
                row = [
                    field.object_name,
                    field.field_label,
                    field.api_name,
                    field.data_type,
                    field.length,
                    field.field_type,
                    field.required,
                    field.formula,
                    field.help_text,
                    field.field_usage
                ]
                all_rows.append(row)
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(all_rows)
        
        self._log_status(f"✅ CSV file created: {output_path}")
        self._log_status(f"✅ Total fields exported: {len(all_rows) - 1}")
        self._log_status("=" * 70)
        
        return output_path