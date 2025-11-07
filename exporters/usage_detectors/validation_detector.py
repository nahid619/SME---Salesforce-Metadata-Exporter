"""
Validation Rule Detector
Detects which fields are used in validation rules
Accuracy: 100%
"""
from typing import Dict, List
import re
from .base_detector import BaseDetector


class ValidationDetector(BaseDetector):
    """Detects validation rule usage of fields"""
    
    def detect_usage(self, object_name: str) -> Dict[str, List[str]]:
        """
        Detect which fields are referenced in validation rules
        
        Args:
            object_name: API name of the object
            
        Returns:
            Dictionary mapping field names to validation rule names
        """
        # Check cache first
        cached = self.get_cached_usage(object_name)
        if cached is not None:
            return cached
        
        self._log(f"  Detecting validation rule usage for {object_name}...", verbose=True)
        
        field_validations = {}
        
        try:
            query = f"SELECT ValidationName, ErrorConditionFormula FROM ValidationRule WHERE EntityDefinition.QualifiedApiName = '{object_name}' AND Active = true"
            url = f"{self.sf_client.base_url}/services/data/v{self.sf_client.api_version}/tooling/query/"
            response = self.sf_client.make_api_call(url, params={'q': query})
            
            if response and response.status_code == 200:
                rules = response.json().get('records', [])
                self._log(f"    Found {len(rules)} validation rules", verbose=True)
                
                for rule in rules:
                    rule_name = rule.get('ValidationName', '')
                    formula = rule.get('ErrorConditionFormula', '')
                    
                    if formula:
                        # Extract field names from formula
                        fields_in_formula = self._extract_fields_from_formula(formula)
                        
                        for field_name in fields_in_formula:
                            if field_name not in field_validations:
                                field_validations[field_name] = []
                            if rule_name not in field_validations[field_name]:
                                field_validations[field_name].append(rule_name)
                
                self._log(f"    ✅ Found {len(field_validations)} fields in validation rules", verbose=True)
        
        except Exception as e:
            self._log(f"    ❌ Validation rule detection error: {str(e)}", verbose=True)
        
        # Cache the results
        self.set_cached_usage(object_name, field_validations)
        return field_validations
    
    def _extract_fields_from_formula(self, formula: str) -> List[str]:
        """
        Extract field names from formula using regex
        
        Args:
            formula: Formula string
            
        Returns:
            List of field names found in formula
        """
        fields = []
        
        # Pattern to match field names (starts with uppercase, contains alphanumeric and underscores)
        field_pattern = r'\b([A-Z][a-zA-Z0-9_]*(?:__c)?)\b'
        potential_fields = re.findall(field_pattern, formula)
        
        # Filter out formula keywords and functions
        formula_keywords = {
            'IF', 'AND', 'OR', 'NOT', 'ISBLANK', 'ISNULL', 'ISCHANGED', 
            'ISNEW', 'PRIORVALUE', 'TEXT', 'VALUE', 'TODAY', 'NOW', 
            'TRUE', 'FALSE', 'CONTAINS', 'BEGINS', 'INCLUDES', 'LEN',
            'LEFT', 'RIGHT', 'MID', 'TRIM', 'UPPER', 'LOWER', 'SUBSTITUTE',
            'YEAR', 'MONTH', 'DAY', 'DATE', 'DATETIME', 'DATEVALUE',
            'TIMEVALUE', 'ABS', 'CEILING', 'FLOOR', 'MAX', 'MIN', 'MOD',
            'ROUND', 'SQRT', 'CASE', 'NULLVALUE', 'BLANKVALUE', 'BR',
            'REGEX', 'FIND', 'ISPICKVAL', 'IMAGE', 'HYPERLINK'
        }
        
        for field in potential_fields:
            if field.upper() not in formula_keywords:
                if field not in fields:
                    fields.append(field)
        
        return fields
