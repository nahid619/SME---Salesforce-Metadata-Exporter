# SME - Features & Capabilities

**Salesforce Metadata Exporter - Complete Feature Documentation**

---

## 🎯 Core Features

### 1. Picklist Data Exporter ✅ **ACTIVE**

Export complete picklist metadata from any Salesforce object with comprehensive details.

#### What It Does
- Extracts all picklist fields from selected objects
- Retrieves both **active** and **inactive** picklist values
- Captures field labels, API names, and value details
- Supports **standard** and **custom** objects
- Handles **multi-select picklists**

#### Output Format
Exported files contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Object** | Object API name | Account |
| **Field Label** | User-friendly field name | Industry |
| **Field API Name** | Technical field name | Industry |
| **Picklist Value Label** | Display value | Technology |
| **Picklist Value API Name** | System value | Technology |
| **Status** | Active or Inactive | Active |

#### Use Cases
- **Metadata Documentation**: Document all picklist values for governance
- **Data Migration**: Prepare picklist mappings for migration projects
- **Compliance Audits**: Track inactive/deprecated values
- **Impact Analysis**: Identify which objects use specific picklist values
- **Training Materials**: Generate picklist reference guides

#### Technical Details
- **API Methods**: Uses multiple Salesforce APIs with fallback
  1. FieldDefinition (Tooling API) - Primary
  2. CustomField with EntityDefinition - Fallback 1
  3. CustomField with object name - Fallback 2
  4. REST API describe - Fallback 3
- **Rate Limiting**: Smart retry logic with exponential backoff
- **Large Dataset Support**: Auto-splits files at Excel/CSV limits
- **Performance**: Processes 10-50 objects/minute (varies by org size)

---

### 2. Dependency Analysis ✅ **ACTIVE**

Analyze object relationships and determine optimal deployment order with isolated analysis focusing only on selected objects.

#### What It Does
- Identifies **Lookup**, **Master-Detail**, and **Junction** relationships
- Analyzes relationships **only between selected objects** (isolated analysis)
- Calculates **deployment levels** (0 = deploy first, 1+ = depends on lower levels)
- Detects **self-referencing** objects (objects that reference themselves)
- Filters out **external dependencies** (relationships to non-selected objects)
- Sorts output by **dependency level first**, then **alphabetically**

#### Output Format
Exported files contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Object API Name** | Object being analyzed | Contact |
| **Dependent Object API Names** | Objects this depends on | Account |
| **Dependency Level** | Deployment order (0, 1, 2, 3...) | 1 |

**Example Output:**
| Object API Name | Dependent Object API Names | Dependency Level |
|-----------------|---------------------------|------------------|
| Account | - | 0 |
| Lead | - | 0 |
| Contact | Account | 1 |
| Custom_Project__c | Account | 1 |
| Opportunity | Account(Contact) | 2 |
| Case | Account(Contact) | 2 |

**Reading the Output:**
- **Level 0**: No dependencies, deploy first
- **Level 1+**: Depends on lower level objects
- **Required**: Master-Detail relationship (must exist)
- **(Optional)**: Lookup relationship (can be null)
- **↻**: Self-reference marker (e.g., Account↻ = Account references itself)
- **Sorted Order**: Objects ordered by level (0, 1, 2...), then alphabetically within each level

#### Use Cases
- **Deployment Planning**: Determine correct deployment order for metadata migration
- **Impact Analysis**: Understand which objects depend on others before making changes
- **Package Development**: Analyze dependencies within your managed/unmanaged package
- **Module Documentation**: Document internal relationships within a feature module
- **Sandbox Setup**: Plan object deployment order for new sandbox configuration
- **Data Migration**: Understand load order for data imports
- **Troubleshooting**: Identify circular dependencies or unexpected relationships

#### Technical Details
- **API Methods**: Uses Salesforce Describe API for relationship metadata
- **Relationship Types Detected**:
  - Lookup (optional references)
  - Master-Detail (required references)
  - Junction Objects (many-to-many via two master-details)
  - Self-References (object references itself)
- **Isolated Analysis**: Only analyzes relationships between selected objects
  - External dependencies (to non-selected objects) are detected and logged
  - Statistics track how many external dependencies were ignored
  - Keeps output clean and focused on your selection
- **Level Calculation**: Uses graph traversal algorithm to determine optimal deployment levels
- **Performance**: Processes 20-100 objects/minute (varies by org complexity)
- **Minimum Requirement**: At least 2 objects must be selected

#### Isolated vs Full Analysis

**What "Isolated" Means:**
- **Shows Only**: Dependencies between your selected objects
- **Ignores**: Dependencies to objects NOT in your selection
- **Example**: If you select Account, Contact, Opportunity:
  - Shows: Contact → Account, Opportunity → Account(Contact)
  - Ignores: Account → User (User not selected)
  - Result: Clean output focused on your selection

**Benefits:**
- ✅ **Cleaner Output**: No external noise
- ✅ **Module-Focused**: Perfect for analyzing specific features/packages
- ✅ **Better Documentation**: Shows only relevant internal relationships
- ✅ **Accurate Levels**: Based on selected objects only
- ✅ **Easy to Understand**: No confusion from external dependencies

**Console Logs Show Ignored Dependencies:**
```
[1/3] Analyzing: Custom_Project__c
  ⊗ Ignored external dependency: Account (not in selection)
  ⊗ Ignored external dependency: User (not in selection)
```

---

## 🔄 Export Capabilities

### Multiple Export Formats

#### Excel (.xlsx)
- **Professional Formatting**:
  - Blue headers with white text
  - Center-aligned column headers
  - Frozen top row for easy scrolling
  - Auto-sized columns for readability
  
- **Auto-splitting**:
  - Creates multiple sheets when exceeding 1,048,576 rows
  - Sheet names: Sheet1, Sheet2, Sheet3...
  - Seamless continuation across sheets

- **Best For**:
  - Documentation and presentations
  - Sharing with non-technical stakeholders
  - Quick analysis with formatting

#### CSV (.csv)
- **Features**:
  - UTF-8 encoding for special characters
  - Proper comma/quote escaping
  - Cross-platform compatible
  
- **Auto-splitting**:
  - Creates multiple files when exceeding 1,000,000 rows
  - File names: filename_1.csv, filename_2.csv...
  - Easy to merge or process separately

- **Best For**:
  - Data analysis in R/Python/SQL
  - Import into databases
  - Integration with other tools
  - Version control (Git-friendly)

---

## 🎨 User Interface Features

### Modern, Intuitive Design

#### Theme Support
- **Dark Mode** (Default):
  - Easy on eyes for long sessions
  - Professional appearance
  - Reduced eye strain
  
- **Light Mode**:
  - Traditional look
  - High contrast for bright environments
  - Toggle anytime with 🌙/☀️ button

#### Window Management
- **Centered Launch**: Always opens in screen center
- **Fixed Resolution**: 1280x720 (optimal for most screens)
- **Resizable**: Drag edges to custom size
- **Fullscreen Mode**: Press F11 for immersive experience
- **Escape Key**: Quick exit from fullscreen

#### Object Selection Interface
- **Dual List Design**:
  - Left panel: Available objects (all queryable objects)
  - Right panel: Selected objects (ready for export)
  - Visual separation for clarity

- **Smart Filters**:
  - **All**: Shows all 500-1000+ objects
  - **Standard**: Shows only Salesforce standard objects (Account, Contact, etc.)
  - **Custom**: Shows only org-specific custom objects (MyCustomObject__c)
  - Instant filtering without reload

- **Search Functionality**:
  - Real-time search as you type
  - Case-insensitive matching
  - Works with filtered results
  - Clears with one click

- **Bulk Operations**:
  - **Select All**: Adds all filtered/searched objects
  - **Deselect All**: Removes all selected objects
  - **Add >>**: Moves selected available objects to export list
  - **<< Remove**: Removes selected objects from export list

#### Visual Feedback
- **Object Counts**: Shows count of items in each list
- **Selection Highlighting**: Light blue background for selected items
- **Button States**: Enabled/disabled based on context
- **Status Colors**:
  - 🟢 Green: Success operations
  - 🟡 Orange: Warnings or in-progress
  - 🔴 Red: Errors or failures

#### Progress Tracking
- **Progress Bar**:
  - Visual bar showing completion percentage
  - Text percentage display (e.g., "45%")
  - Smooth animation during export
  
- **Status Bar**:
  - Shows current operation (e.g., "Processing Account...")
  - Color-coded status messages
  - Updates in real-time
  
- **Terminal/Console**:
  - Scrollable log output
  - Timestamps on every message [HH:MM:SS]
  - Readable Consolas 12pt font
  - Auto-scrolls to latest message
  - Detailed progress logs

---

## 🔧 Technical Features

### Salesforce API Integration

#### Connection Management
- **Auto API Version Detection**: Automatically uses latest API version
- **Session Management**: Maintains secure session throughout use
- **Timeout Handling**: 30-second timeout per request
- **Connection Validation**: Verifies connection before operations

#### Query Optimization
- **Multiple Query Methods**: 4 fallback strategies for maximum compatibility
- **Batch Processing**: Processes objects one at a time with progress updates
- **Rate Limit Handling**:
  - Automatic retry on rate limit errors
  - Exponential backoff (1s, 2s, 4s delays)
  - Maximum 3 retry attempts
  - Graceful degradation

#### Error Handling
- **Comprehensive Try-Catch**: Every API call wrapped in error handling
- **Detailed Error Messages**: Clear description of what went wrong
- **Partial Success Support**: Continues processing other objects if one fails
- **Error Logging**: All errors logged to terminal with context

### Data Processing

#### Metadata Parsing
- **Field Type Detection**: Identifies all picklist types
- **Value Status Detection**: Distinguishes active vs inactive values
- **Dependent Picklist Support**: Handles controlling/dependent fields
- **Record Type Awareness**: Captures record type specific values

#### Data Transformation
- **Standardized Output**: Consistent format across all exports
- **Null Handling**: Properly handles missing/null values
- **Special Character Escaping**: Correct CSV/Excel formatting
- **Large Dataset Management**: Memory-efficient processing

### File Operations

#### Smart File Handling
- **Automatic Splitting**: No manual intervention needed for large exports
- **Naming Convention**: Clear, timestamped filenames
- **Format Preservation**: Maintains Excel formatting in splits
- **UTF-8 Encoding**: Supports international characters

#### Excel-Specific Features
- **Workbook Management**: Creates sheets as needed
- **Style Application**: Professional formatting on all sheets
- **Column Sizing**: Auto-fits content width
- **Row Freezing**: Keeps headers visible while scrolling

---

## 📊 Statistics & Reporting

### Export Summary
After each export, view detailed statistics:

```
=== Export Statistics ===
Total Runtime: HH:MM:SS
API Calls Made: X
Objects Processed: X/Y
  ✓ Successful: X
  ✗ Failed: Y
Total Picklist Fields: X
Total Picklist Values: X
  - Active: X
  - Inactive: X
```

### Real-Time Metrics
During export, monitor:
- Current object being processed
- Progress percentage
- Elapsed time
- Objects completed / total objects
- API calls made so far

---

## 🔒 Security Features

### Credential Management
- **No Storage**: Credentials never saved to disk
- **Memory Only**: Stored in memory during active session
- **Secure Transmission**: HTTPS for all API calls
- **Session Timeout**: Auto-expires after inactivity
- **Clean Logout**: Clears all credentials from memory

### API Security
- **Token-Based Authentication**: Uses Salesforce security tokens
- **Session Management**: Secure session handling
- **IP Restriction Compliance**: Works with Salesforce IP restrictions
- **Permission Respect**: Only accesses data user can see

---

## ⚡ Performance Features

### Optimization Strategies
- **Threaded Operations**: UI never freezes during export
- **Progressive Loading**: Objects load as they're retrieved
- **Efficient Queries**: Minimizes API calls
- **Memory Management**: Handles large datasets without memory issues

### Scalability
- **Small Orgs (1-50 objects)**: Export in seconds
- **Medium Orgs (50-500 objects)**: Export in minutes
- **Large Orgs (500+ objects)**: Progressively processes all objects
- **No Hard Limits**: Can handle any size Salesforce org

---

## 🎮 User Experience Features

### Ease of Use
- **One-Click Operations**: Most tasks require single click
- **Smart Defaults**: Sensible default selections
- **Undo Support**: Easy to remove incorrect selections
- **Clear Instructions**: Intuitive button labels
- **Keyboard Shortcuts**: F11 fullscreen, Enter to login

### Accessibility
- **Readable Fonts**: Large, clear text
- **High Contrast**: Good visibility in all themes
- **Keyboard Navigation**: Full keyboard support
- **Clear Feedback**: Always know what's happening
- **Error Recovery**: Clear paths to fix issues

### Workflow Support
- **Save Session State**: Remember org connection during session
- **Cancel Anytime**: Stop long-running exports
- **Multiple Attempts**: Retry failed operations easily
- **Batch Operations**: Process multiple objects efficiently

---

## 🚀 Coming Soon (Planned Features)

### 1. Metadata Exporter 🔜
**What It Will Do:**
- Export comprehensive object metadata
- Include field types, lengths, descriptions
- Capture validation rules
- Document page layouts
- Export permission sets/profiles

**Use Cases:**
- Complete org documentation
- Metadata backup
- Sandbox configuration
- Compliance documentation

### 3. Formula Fields Extractor 🔜
**What It Will Do:**
- Extract all formula fields
- Show formula syntax
- Identify field dependencies
- Highlight complex formulas
- Export for analysis

**Use Cases:**
- Formula documentation
- Complex formula review
- Migration preparation
- Performance analysis

---

## 💡 Tips & Best Practices

### Maximizing Efficiency

**For Daily Use:**
1. Keep application open during work day
2. Use filters to narrow object lists
3. Create export templates (saved object selections)
4. Regular exports for change tracking

**For Large Orgs:**
1. Use Standard/Custom filters first
2. Search for specific objects
3. Export in batches (50-100 objects)
4. Schedule exports during low-traffic times

**For Documentation:**
1. Use Excel format for formatted reports
2. Add export date to filename
3. Store in version-controlled folder
4. Review statistics for completeness

### Performance Optimization

**Faster Exports:**
- Stable, fast internet connection
- Close unnecessary applications
- Use CSV for raw data needs
- Filter objects before selecting all

**API Limit Management:**
- Monitor daily API usage in Salesforce
- Space out large exports
- Use off-peak hours for big exports
- Track API calls in export statistics

---

## 📈 Success Metrics

### What Makes a Good Export

✅ **Complete**: All selected objects processed  
✅ **Accurate**: Matches Salesforce UI values  
✅ **Fast**: Reasonable completion time  
✅ **Reliable**: No unexpected failures  
✅ **Clear**: Easy to understand output  

### Typical Performance

| Org Size | Objects | Export Time | API Calls |
|----------|---------|-------------|-----------|
| Small | 10 | 30 sec | 15 |
| Medium | 50 | 2-3 min | 75 |
| Large | 200 | 8-12 min | 300 |
| Enterprise | 500+ | 20-40 min | 750+ |

*Times vary based on internet speed, API limits, and object complexity*

---

## 🎯 Feature Comparison

### Why Choose SME?

| Feature | SME | Salesforce UI | Other Tools |
|---------|-----|---------------|-------------|
| **Bulk Export** | ✅ Multiple objects | ❌ One at a time | ⚠️ Limited |
| **Inactive Values** | ✅ Included | ❌ Not shown | ⚠️ Sometimes |
| **Auto-splitting** | ✅ Automatic | ❌ Manual | ❌ Manual |
| **Progress Tracking** | ✅ Real-time | ❌ None | ⚠️ Basic |
| **Format Options** | ✅ Excel + CSV | ⚠️ CSV only | ⚠️ Varies |
| **Offline Use** | ✅ Desktop app | ❌ Web only | ⚠️ Varies |
| **Cost** | ✅ Free | ✅ Free | ⚠️ Often paid |

---

## 🔧 Customization Capabilities

### What You Can Customize

#### Visual Settings
- Window dimensions
- Theme colors
- Font sizes
- Terminal height
- Button colors

#### Behavior Settings
- API retry attempts
- Request timeouts
- File size limits
- Split thresholds
- Auto-scroll behavior

#### Export Settings
- Default format (Excel/CSV)
- Filename patterns
- Column ordering
- Header formatting
- Encoding preferences

*See README.md for customization instructions*

---

## ✅ Feature Status Summary

### ✅ Currently Available
- Picklist data export (standard & custom objects)
- **Dependency analysis with isolated mode** ✨ **NEW!**
- **Deployment level calculation** ✨ **NEW!**
- **Relationship type detection (Lookup/Master-Detail/Junction)** ✨ **NEW!**
- Multiple export formats (Excel & CSV)
- Theme toggle (dark/light)
- Object filtering (All/Standard/Custom)
- Search functionality
- Bulk operations (Select All/Deselect All)
- Progress tracking
- Export cancellation
- Detailed statistics reporting
- Fullscreen mode
- Auto-splitting for large datasets

### 🔜 Coming Soon
- Comprehensive metadata export
- Formula field extraction

### 💡 Under Consideration
- Export scheduling
- Automated backups
- Change detection
- API usage analytics
- Custom report templates
- Dependency visualization diagrams

---

**Version:** 2.0.0  
**Last Updated:** 2025

**More features coming based on user feedback!**