"""
SME - Dependency Analyzer Module (FIXED - Proper User & System Object Handling)
Analyzes dependencies ONLY between selected objects
"""
import threading
from typing import List, Dict, Optional, Tuple, Callable, Set
from collections import defaultdict, deque
from core.salesforce_client import SalesforceClient
from utils.file_handler import FileHandler


class ObjectDependency:
    """Represents a single object dependency relationship"""
    def __init__(self, child_object: str, parent_object: str, 
                 field_name: str, relationship_type: str, is_required: bool):
        self.child_object = child_object
        self.parent_object = parent_object
        self.field_name = field_name
        self.relationship_type = relationship_type  # 'Lookup', 'MasterDetail'
        self.is_required = is_required


class DependencyAnalyzer:
    """Analyzes and exports Salesforce object dependencies (ISOLATED MODE)"""
    
    def __init__(self, sf_client: SalesforceClient, status_callback: Optional[Callable] = None):
        """
        Initialize dependency analyzer
        
        Args:
            sf_client: Salesforce client instance
            status_callback: Optional callback for status updates
        """
        self.sf_client = sf_client
        self.status_callback = status_callback
        self.cancel_event = threading.Event()
        self.file_handler = FileHandler(log_callback=self._log_status)
        
        # Dependency graph storage
        self.dependencies: List[ObjectDependency] = []
        self.object_levels: Dict[str, int] = {}
        
        # System objects that typically have no dependencies
        self.system_base_objects = {'User', 'RecordType', 'Profile', 'UserRole'}
    
    def _log_status(self, message: str, verbose: bool = False):
        """Internal logging helper"""
        if self.status_callback:
            self.status_callback(message, verbose=verbose)
    
    def cancel_analysis(self):
        """Signal cancellation of the analysis"""
        self.cancel_event.set()
        self._log_status("🛑 Cancel requested by user...")
    
    def analyze_dependencies(self, object_names: List[str], output_path: str,
                           export_format: str = "excel",
                           progress_callback: Optional[Callable] = None) -> Tuple[str, Dict]:
        """
        Analyze object dependencies (ISOLATED - only between selected objects)
        
        Args:
            object_names: List of object API names to analyze
            output_path: Path to save the output file
            export_format: 'excel' or 'csv'
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (output_path, statistics_dict)
        """
        self.cancel_event.clear()
        self.sf_client.api_call_count = 0
        
        self._log_status("=" * 70)
        self._log_status("=== Starting Dependency Analysis (Isolated Mode) ===")
        self._log_status("=" * 70)
        self._log_status(f"Total objects to analyze: {len(object_names)}")
        self._log_status(f"Using API version: v{self.sf_client.api_version}")
        self._log_status(f"Mode: ISOLATED (only analyzing dependencies between selected objects)")
        self._log_status("")
        
        # Create a set for fast lookup
        selected_objects_set = set(object_names)
        
        stats = {
            'total_objects': len(object_names),
            'analyzed_objects': 0,
            'failed_objects': 0,
            'total_dependencies': 0,
            'lookup_dependencies': 0,
            'master_detail_dependencies': 0,
            'self_references': 0,
            'ignored_external_dependencies': 0,
            'max_dependency_level': 0,
            'failed_details': [],
            'cancelled': False,
            'api_calls_made': 0
        }
        
        # Step 1: Collect all dependencies (ONLY between selected objects)
        self._log_status("Step 1: Collecting relationship data (isolated mode)...")
        for i, obj_name in enumerate(object_names, 1):
            if self.cancel_event.is_set():
                self._log_status("🛑 Analysis cancelled by user")
                stats['cancelled'] = True
                break
            
            if progress_callback:
                progress_callback(i, len(object_names))
            
            self._log_status(f"[{i}/{len(object_names)}] Analyzing: {obj_name}")
            
            try:
                ignored_count = self._analyze_object_relationships(obj_name, selected_objects_set)
                stats['ignored_external_dependencies'] += ignored_count
                stats['analyzed_objects'] += 1
            except Exception as e:
                self._log_status(f"  ❌ ERROR: {str(e)}")
                stats['failed_objects'] += 1
                stats['failed_details'].append({'name': obj_name, 'reason': str(e)})
        
        if self.cancel_event.is_set():
            stats['cancelled'] = True
            self._log_status("")
            self._log_status("🛑 Analysis was cancelled. Partial data will be saved.")
        
        # Step 2: Calculate dependency levels
        self._log_status("")
        self._log_status("Step 2: Calculating dependency levels (isolated)...")
        self._calculate_dependency_levels(object_names, selected_objects_set)
        
        # Step 3: Compile statistics
        stats['total_dependencies'] = len(self.dependencies)
        stats['lookup_dependencies'] = sum(1 for d in self.dependencies if d.relationship_type == 'Lookup')
        stats['master_detail_dependencies'] = sum(1 for d in self.dependencies if d.relationship_type == 'MasterDetail')
        stats['self_references'] = sum(1 for d in self.dependencies if d.child_object == d.parent_object)
        stats['max_dependency_level'] = max(self.object_levels.values()) if self.object_levels else 0
        stats['api_calls_made'] = self.sf_client.api_call_count
        
        # Step 4: Create output file
        self._log_status("")
        self._log_status("Step 3: Creating output file...")
        self._log_status(f"  Total dependencies found (between selected objects): {stats['total_dependencies']}")
        self._log_status(f"  External dependencies ignored: {stats['ignored_external_dependencies']}")
        
        rows = self._build_output_rows(object_names)
        
        if export_format == "csv":
            final_output_path = self.file_handler.create_csv_file(rows, output_path)
        else:
            final_output_path = self.file_handler.create_excel_file(rows, output_path)
        
        self._log_status("=" * 70)
        return final_output_path, stats
    
    def _analyze_object_relationships(self, object_name: str, selected_objects_set: Set[str]) -> int:
        """
        Analyze all relationship fields for a single object (ISOLATED MODE)
        Only records dependencies to objects IN the selected set
        
        Returns:
            Number of external dependencies ignored
        """
        ignored_count = 0
        
        try:
            # Get object describe
            obj_describe = self.sf_client.describe_object(object_name)
            
            # Find all relationship fields
            for field in obj_describe['fields']:
                field_type = field.get('type', '')
                field_name = field.get('name', '')
                
                # Check for Lookup or MasterDetail (reference type)
                if field_type in ['reference']:
                    reference_to = field.get('referenceTo', [])
                    is_required = field.get('nillable', True) == False
                    
                    # Check if it's Master-Detail (multiple methods for reliability)
                    # Method 1: Check relationshipOrder (most reliable)
                    relationship_order = field.get('relationshipOrder')
                    
                    # Method 2: Check cascadeDelete (backup)
                    cascade_delete = field.get('cascadeDelete', False)
                    
                    # Method 3: Check if field is required and has delete cascade behavior
                    # Master-Detail fields are always required (nillable=False)
                    is_master_detail = (relationship_order is not None and relationship_order >= 0) or \
                                      (cascade_delete and not field.get('nillable', True))
                    
                    relationship_type = 'MasterDetail' if is_master_detail else 'Lookup'
                    
                    # Process each referenced object
                    for parent_obj in reference_to:
                        # CRITICAL: Only add dependency if parent is in selected objects
                        if parent_obj in selected_objects_set:
                            # Skip standard system fields that don't represent real dependencies
                            if self._should_skip_field(field_name, parent_obj):
                                self._log_status(f"  ⊘ Skipped system field: {field_name} → {parent_obj}", verbose=True)
                                continue
                            
                            dependency = ObjectDependency(
                                child_object=object_name,
                                parent_object=parent_obj,
                                field_name=field_name,
                                relationship_type=relationship_type,
                                is_required=is_required
                            )
                            self.dependencies.append(dependency)
                            
                            if object_name == parent_obj:
                                self._log_status(f"  ↻ Self-reference: {field_name}")
                            else:
                                req_label = "Required" if is_required else "Optional"
                                self._log_status(f"  → {parent_obj} ({relationship_type}, {req_label}) via {field_name}")
                        else:
                            # External dependency - ignore it
                            ignored_count += 1
                            self._log_status(f"  ⊗ Ignored external: {field_name} → {parent_obj} (not in selection)", verbose=True)
        
        except Exception as e:
            self._log_status(f"  ERROR analyzing relationships: {str(e)}")
            raise
        
        return ignored_count
    
    def _should_skip_field(self, field_name: str, parent_obj: str) -> bool:
        """
        Determine if a field should be skipped for dependency analysis
        Skips audit fields and system tracking fields
        """
        # Audit and system tracking fields to skip
        skip_fields = {
            'OwnerId', 'CreatedById', 'LastModifiedById', 
            'RecordTypeId', 'ProfileId'
        }
        
        # Skip if it's a system tracking field
        if field_name in skip_fields:
            return True
        
        # Don't skip business-relevant User lookups
        # Only skip if it's clearly an audit/tracking field
        if parent_obj == 'User' and field_name.lower() in ['ownerid', 'createdbyid', 'lastmodifiedbyid']:
            return True
        
        return False
    
    def _calculate_dependency_levels(self, object_names: List[str], selected_objects_set: Set[str]):
        """
        Calculate dependency levels for all objects (ISOLATED)
        Level 0: No dependencies (within selected objects) OR system base objects
        Level 1: Depends only on Level 0
        Level 2: Depends on Level 0 or 1
        Level N: Max(parent levels) + 1
        """
        # Build adjacency list (child -> list of parents)
        graph: Dict[str, Set[str]] = defaultdict(set)
        in_degree: Dict[str, int] = defaultdict(int)
        
        # Initialize all objects with in-degree 0
        for obj in object_names:
            if obj not in in_degree:
                in_degree[obj] = 0
        
        # Build graph (only dependencies between selected objects)
        for dep in self.dependencies:
            child = dep.child_object
            parent = dep.parent_object
            
            # Skip self-references for level calculation
            if child == parent:
                continue
            
            # Add edge
            if parent not in graph[child]:
                graph[child].add(parent)
                in_degree[child] += 1
        
        # Topological sort to calculate levels
        queue = deque()
        
        # Start with objects that have no dependencies (Level 0)
        # Also include system base objects at Level 0
        for obj in object_names:
            if in_degree[obj] == 0 or obj in self.system_base_objects:
                queue.append(obj)
                self.object_levels[obj] = 0
                reason = "(system base object)" if obj in self.system_base_objects else "(no dependencies)"
                self._log_status(f"  Level 0: {obj} {reason}")
        
        # Process objects level by level
        processed = set()
        while queue:
            current_obj = queue.popleft()
            if current_obj in processed:
                continue
            processed.add(current_obj)
            
            current_level = self.object_levels[current_obj]
            
            # Check all objects that depend on current_obj
            for child_obj in object_names:
                if child_obj in processed:
                    continue
                    
                if current_obj in graph[child_obj]:
                    # Calculate child's level based on ALL its parents
                    all_parents_resolved = True
                    parent_levels = []
                    
                    for parent in graph[child_obj]:
                        if parent in self.object_levels:
                            parent_levels.append(self.object_levels[parent])
                        else:
                            all_parents_resolved = False
                    
                    # Only set level if all parents have been resolved
                    if all_parents_resolved and parent_levels:
                        child_level = max(parent_levels) + 1
                        
                        # Update level if not set or if new level is higher
                        if child_obj not in self.object_levels:
                            self.object_levels[child_obj] = child_level
                            self._log_status(f"  Level {child_level}: {child_obj}")
                        elif self.object_levels[child_obj] < child_level:
                            old_level = self.object_levels[child_obj]
                            self.object_levels[child_obj] = child_level
                            self._log_status(f"  Level {child_level}: {child_obj} (updated from {old_level})")
                        
                        # Add to queue if not already there
                        if child_obj not in processed:
                            queue.append(child_obj)
        
        # Handle objects not yet assigned (isolated or only self-referencing)
        for obj in object_names:
            if obj not in self.object_levels:
                self.object_levels[obj] = 0
                self._log_status(f"  Level 0: {obj} (isolated within selection)")
    
    def _build_output_rows(self, object_names: List[str]) -> List[List[str]]:
        """
        Build output rows (ISOLATED MODE - only selected objects appear)
        Format: Object API Name | Dependent Object API Names | Dependency Level
        
        Dependencies format: Required1, Required2(Optional1, Optional2)
        Output sorted by: Dependency Level (ascending), then Object Name (alphabetically)
        """
        # Header row
        rows = [['Object API Name', 'Dependent Object API Names', 'Dependency Level']]
        
        # Group dependencies by child object
        obj_deps: Dict[str, Dict[str, List[ObjectDependency]]] = defaultdict(lambda: defaultdict(list))
        
        # Only include dependencies where BOTH child and parent are in selected objects
        for dep in self.dependencies:
            if dep.child_object in object_names and dep.parent_object in object_names:
                obj_deps[dep.child_object][dep.parent_object].append(dep)
        
        # Build data rows for each object (unsorted first)
        data_rows = []
        
        for obj_name in object_names:
            level = self.object_levels.get(obj_name, 0)
            
            if obj_name not in obj_deps or not obj_deps[obj_name]:
                # No dependencies (within selected objects)
                data_rows.append([obj_name, '-', level])
            else:
                # Collect required and optional dependencies
                required_deps = set()
                optional_deps = set()
                
                for parent_obj, deps_list in obj_deps[obj_name].items():
                    # Check if any dependency to this parent is required
                    has_required = any(d.is_required or d.relationship_type == 'MasterDetail' 
                                     for d in deps_list)
                    
                    # Check for self-reference
                    if parent_obj == obj_name:
                        parent_obj = f"{parent_obj}↻"
                    
                    if has_required:
                        required_deps.add(parent_obj)
                    else:
                        optional_deps.add(parent_obj)
                
                # Format: Required1, Required2(Optional1, Optional2)
                parts = []
                if required_deps:
                    parts.append(', '.join(sorted(required_deps)))
                if optional_deps:
                    parts.append(f"({', '.join(sorted(optional_deps))})")
                
                dependent_objects_str = ''.join(parts) if parts else '-'
                
                data_rows.append([obj_name, dependent_objects_str, level])
        
        # Sort by Dependency Level (ascending), then by Object Name (alphabetically)
        data_rows.sort(key=lambda row: (row[2], row[0]))
        
        # Add sorted data rows to output
        rows.extend(data_rows)
        
        return rows