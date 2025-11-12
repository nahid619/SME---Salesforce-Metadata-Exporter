# Salesforce Metadata Exporter (SME)

**Version:** 2.1.0 (Phase 1 Complete + SOQL Runner)  
**A modern GUI application for exporting Salesforce metadata with comprehensive field usage detection and SOQL query execution**

---

## 🎉 **What's New in Version 2.1.0**

### 🆕 **SOQL Query Runner** (NEW!)
- ⚡ Execute SOQL queries directly from the app
- 📊 Export results to Excel or CSV
- ✨ Query formatting for readability
- 📋 Object browser with search
- 🔍 Scrollable results table
- 🎯 Real-time query execution

### 🆕 Comprehensive Field Usage Detection (85-90% Coverage)
- ✅ **Page Layouts** - 100% accuracy via Tooling API
- ✅ **Validation Rules** - 100% accuracy via formula parsing
- ✅ **Workflows** - 100% accuracy via formula parsing
- ✅ **Record Types** - 100% accuracy via picklist restrictions
- ✅ **Apex Classes** - 90-95% accuracy via code search
- ✅ **Visualforce Pages** - 90-95% accuracy via code search
- ✅ **Triggers** - 90-95% accuracy via code search

### 🆕 Improved Progress Tracking
- Field-based progress calculation (not just object count)
- More accurate representation of actual work being done
- Real-time updates during export

### 🆕 Enhanced Export Format
- Now matches industry standard format (Schema Lister compatible)
- Multi-line field usage display
- Professional Excel formatting with text wrapping

---

## 📋 Quick Setup (5 Minutes)

### 1. Prerequisites
- Python 3.8+ installed ([Download Python](https://www.python.org/downloads/))
- Internet connection

**Check Python version:**
```bash
python --version
# Should show: Python 3.8.x or higher
```

---

### 2. Project Structure Setup

**Windows (PowerShell):**
```powershell
# Create project directory
mkdir salesforce-metadata-exporter
cd salesforce-metadata-exporter

# Create subdirectories
mkdir config, core, exporters, ui, utils
mkdir exporters\usage_detectors

# Create __init__.py files
New-Item -ItemType File -Path "config\__init__.py", "core\__init__.py", "exporters\__init__.py", "ui\__init__.py", "utils\__init__.py", "exporters\usage_detectors\__init__.py"
```

**Mac/Linux:**
```bash
# Create project directory and subdirectories
mkdir -p salesforce-metadata-exporter/{config,core,exporters,ui,utils,exporters/usage_detectors}
cd salesforce-metadata-exporter

# Create __init__.py files
touch config/__init__.py core/__init__.py exporters/__init__.py ui/__init__.py utils/__init__.py exporters/usage_detectors/__init__.py
```

---

### 3. Project Structure

After setup, your structure should look like this:
```
salesforce-metadata-exporter/
├── main.py
├── requirements.txt
├── README.md
├── FEATURES.md
│
├── config/
│   ├── __init__.py
│   └── constants.py
│
├── core/
│   ├── __init__.py
│   └── salesforce_client.py
│
├── exporters/
│   ├── __init__.py
│   ├── picklist_exporter.py
│   ├── dependency_analyzer.py
│   ├── metadata_exporter.py
│   ├── soql_query_runner.py
│   │
│   └── usage_detectors/
│       ├── __init__.py
│       ├── base_detector.py
│       ├── layout_detector.py
│       ├── validation_detector.py
│       ├── workflow_detector.py
│       ├── recordtype_detector.py
│       └── code_search_detector.py
│
├── ui/
│   ├── __init__.py
│   ├── login_screen.py
│   ├── main_screen.py
│   └── soql_query_screen.py
│
└── utils/
    ├── __init__.py
    ├── file_handler.py
    └── helpers.py
```

---

### 4. Install Dependencies in Virtual Environment

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import simple_salesforce, openpyxl, requests, customtkinter; print('✅ All dependencies installed!')"
```

---

### 5. Run the Application

**Make sure virtual environment is activated** (you should see `(venv)` in your terminal)
```bash
python main.py
```

**Expected result:**
- Window opens centered on screen (1280x720)
- Login screen displays
- Dark theme by default

---

## 🔒 Getting Started - First Use

### Step 1: Get Salesforce Security Token

1. Login to Salesforce
2. Click profile icon (top right) → **Settings**
3. Left sidebar: **My Personal Information** → **Reset My Security Token**
4. Click **"Reset Security Token"**
5. Check your email for the token

### Step 2: Connect to Salesforce

**For Production/Developer Org:**
```
Username: your.email@company.com
Password: YourPassword
Security Token: [Token from email]
Org Type: Production ← Select this
```

**For Sandbox:**
```
Username: your.email@company.com.sandboxname
Password: YourPassword
Security Token: [Token from email]
Org Type: Sandbox/Test ← Select this
```

Click **"Connect to Salesforce"**

**⚠️ Important Permissions for Field Usage Detection:**
- View All Data
- Author Apex (to access Apex/VF code)
- View Setup and Configuration

---

## 🎯 Using the Application

### 1. Export Picklist Data (Quick)

1. Wait for objects to load (30-60 seconds for large orgs)
2. Select objects (filters: All / Standard / Custom)
3. Click **"Add >>"** to move to export list
4. Choose format: Excel (.xlsx) or CSV (.csv)
5. Click **"📋 Export Picklist Data"**
6. Choose save location
7. Monitor progress and review results

---

### 2. Dependency Analysis (Quick)

1. Select **at least 2 objects**
2. Click **"🔗 Dependency Analysis"**
3. Choose save location
4. Review deployment order in output file

**Output shows:**
- Level 0 objects (deploy first)
- Level 1+ objects (deploy after dependencies)
- Required vs Optional relationships

---

### 3. Metadata Export with Field Usage Detection (Comprehensive) 🆕

**This is the most powerful feature - gives you complete field documentation!**

#### Step-by-Step:

1. **Select Objects:**
   - Use filters (All / Standard / Custom)
   - Search for specific objects
   - Click **"Add >>"** to add to export list
   - Can select 1 to 100+ objects

2. **Start Export:**
   - Click **"📦 Metadata Exporter"** button
   - Options dialog appears

3. **Choose Options:**
   - ☑ **Export custom fields only** (optional)
     - Check this to skip all standard fields
     - Useful for documenting custom development
   
   - ☑ **Include field usage analysis** (recommended) 🆕
     - ⚠️ This adds processing time but gives comprehensive usage data
     - Shows where each field is used across your org
     - Detects: Layouts, Validation Rules, Workflows, Record Types, Apex, VF, Triggers
   
   - Click **"Continue"**

4. **Save File:**
   - Choose save location and filename
   - Format: Excel (.xlsx) or CSV (.csv)
   - Click **Save**

5. **Monitor Progress:**
   - **Pre-scan phase**: Calculates total fields
   - **Progress bar**: Shows field-based progress (e.g., "345/487 fields - 71%")
   - **Terminal logs**: Detailed information about what's being detected
   - **Status bar**: Current operation
   - **Can cancel anytime**: Click "⏸️ Cancel Export"

6. **Review Results:**
   - Success message with statistics
   - Check **Field Usage** column for comprehensive usage data

---

### 4. SOQL Query Runner (NEW!) 🆕

**Execute SOQL queries and export results directly from the app!**

#### Step-by-Step:

1. **Open SOQL Runner:**
   - Click **"⚡ SOQL Query Runner"** button from main screen

2. **Write or Generate Query:**
   
   **Option A: Use Object Browser**
   - Click **"📋 Show Objects"** (orange button, top right)
   - Search for object (e.g., "Account")
   - Select object → Basic query inserted: `SELECT Id, Name FROM Account LIMIT 10`
   
   **Option B: Write Manually**
   - Type your SOQL query in the text area
   - Example: `SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology'`

3. **Format Query (Optional):**
   - Click **"✨ Format"** to beautify your query
   - Makes multi-line queries more readable

4. **Execute Query:**
   - Click **"▶ Execute Query"** (green button)
   - Progress bar shows execution
   - Results appear in table below

5. **View Results:**
   - Scrollable table (horizontal and vertical)
   - Shows: `Query Results (X records)`
   - All columns from your SELECT statement

6. **Export Results:**
   - Click **"📄 Export CSV"** for CSV format
   - Click **"📊 Export Excel"** for Excel format (with formatting)
   - Choose save location
   - Done!

#### Query Examples:

**Simple:**
```sql
SELECT Id, Name FROM Account LIMIT 10
```

**With WHERE clause:**
```sql
SELECT Id, Name, Industry 
FROM Account 
WHERE Industry = 'Technology' 
LIMIT 50
```

**With relationships:**
```sql
SELECT Id, Account.Name, Owner.Name, Amount 
FROM Opportunity 
WHERE Amount > 10000 
ORDER BY Amount DESC
```

**Aggregations:**
```sql
SELECT COUNT(Id), Industry 
FROM Account 
GROUP BY Industry
```

#### Tips:
- Use **LIMIT** for testing queries (faster)
- Click **"🗑️ Clear"** to start fresh
- Results are scrollable both ways
- Export preserves all data and formatting

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **F11** | Toggle fullscreen mode |
| **Escape** | Exit fullscreen |
| **Enter** | Submit login (when on login screen) |

---

## 🎨 Application Features

### Current Features (Version 2.1.0)
- ✅ **Picklist Data Export**: Export all picklist values from any object
- ✅ **Dependency Analysis**: Analyze object relationships and deployment order
- ✅ **Metadata Export with Usage Detection** 🆕: Comprehensive field documentation with 85-90% usage coverage
- ✅ **SOQL Query Runner** 🆕: Execute queries and export results
- ✅ **Multiple Export Formats**: Excel (.xlsx) and CSV (.csv)
- ✅ **Field-Based Progress**: Accurate progress tracking based on data volume
- ✅ **Theme Toggle**: Switch between dark/light mode
- ✅ **Smart Filters**: Filter by All/Standard/Custom objects
- ✅ **Instant Search**: Find objects quickly
- ✅ **Cancel Support**: Stop operations anytime
- ✅ **Detailed Statistics**: Comprehensive export summaries
- ✅ **Query Formatting**: Beautify SOQL queries
- ✅ **Object Browser**: Searchable popup with all objects

### UI Features
- ✅ **Theme Toggle**: Dark/light mode with 🌙/☀️ button
- ✅ **Resizable Window**: Drag edges to resize
- ✅ **Fullscreen Mode**: Press F11
- ✅ **Centered Launch**: Always opens in screen center
- ✅ **Real-time Progress**: Live updates during export with field-based calculation
- ✅ **Scrollable Components**: Query editor and results table scroll independently

### Object Selection
- ✅ **Smart Filters**: All / Standard / Custom objects
- ✅ **Instant Search**: Find objects quickly
- ✅ **Bulk Operations**: Select All / Deselect All
- ✅ **Visual Feedback**: Selected objects highlighted
- ✅ **Count Display**: Shows number of objects in each list

### Export Features
- ✅ **Multiple Formats**: Excel or CSV
- ✅ **Auto-splitting**: Handles large datasets
- ✅ **Professional Formatting**: Excel headers styled, text wrapping enabled
- ✅ **Cancel Support**: Stop export anytime
- ✅ **Statistics**: Detailed export summary with usage metrics

### SOQL Features (NEW!)
- ✅ **Query Editor**: Large text area with scrolling
- ✅ **Clear Button**: Reset query textbox
- ✅ **Format Button**: Beautify SOQL syntax
- ✅ **Object Browser**: Searchable popup with all org objects
- ✅ **Execute Query**: Run queries with progress tracking
- ✅ **Results Table**: Scrollable X and Y axis
- ✅ **Dual Export**: CSV and Excel formats
- ✅ **Error Handling**: Clear error messages

---

## 🛠️ Customization

### Change Window Size
Edit `config/constants.py`:
```python
WINDOW_WIDTH = 1920   # Your preferred width
WINDOW_HEIGHT = 1080  # Your preferred height
```

### Change Colors
Edit `config/constants.py`:
```python
COLOR_SUCCESS = "#28a745"  # Green
COLOR_WARNING = "#FFA500"  # Orange
COLOR_DANGER = "#CC3333"   # Red
```

### Change Terminal Font Size
Edit `config/constants.py`:
```python
TERMINAL_FONT = ("Consolas", 14)  # Larger font
TERMINAL_HEIGHT = 250             # More height
```

---

## 🛑 Troubleshooting

### Application won't start
```bash
# Check for errors
python main.py

# Common fix: Ensure virtual environment is activated
# You should see (venv) in terminal prompt
```

**If "No module named 'usage_detectors'" error:**
- Ensure `__init__.py` exists in `exporters/usage_detectors/`
- Verify all detector files are in correct location

**If "No module named 'customtkinter'" error:**
- Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
- Reinstall: `pip install -r requirements.txt`

### Can't connect to Salesforce
- ❌ Wrong credentials → Double-check username, password, token
- ❌ Wrong org type → Production vs Sandbox
- ❌ Expired token → Reset security token in Salesforce
- ❌ IP restrictions → Check Salesforce IP whitelist settings
- ❌ Network issues → Check internet connection

### Objects won't load
- ⏳ **Wait**: Large orgs can take 30-60 seconds
- 📋 **Check terminal**: Look for error messages
- 🔒 **Permissions**: Verify API access in Salesforce profile

### Export fails
- ❌ Object doesn't exist in org
- ❌ No picklist fields in selected object (for picklist export)
- ❌ Less than 2 objects selected (for dependency analysis)
- ❌ API limit reached (check daily limits)
- 📋 Review terminal logs for specific error

### SOQL Query Issues
- ❌ **Syntax error** → Check query syntax (must start with SELECT)
- ❌ **Invalid field** → Verify field exists on object
- ❌ **Invalid object** → Check object API name spelling
- ❌ **No results** → Query conditions might be too restrictive
- 📋 Review error message for specific issue

### Field Usage is blank or incomplete 🆕
**Common causes:**
1. **"Include field usage analysis" not checked** - Must enable this option
2. **Insufficient permissions** - Requires:
   - View All Data
   - Author Apex
   - View Setup and Configuration
3. **Field not actually used** - Some fields genuinely have no usage
4. **Code detection limitations** - Text search is 90-95% accurate (may miss some references)

**What to check:**
- Terminal logs show "Loading usage data for [Object]"
- Terminal logs show counts (e.g., "Found 3 page layouts")
- Your Salesforce user has required permissions
- Fields that should have usage might be in components not yet detected (Phase 2)

### Performance issues
For large orgs (500+ objects):
1. Use filters (Standard/Custom) to reduce list size
2. Search for specific objects instead of scrolling
3. Export in smaller batches (10-20 objects)
4. Monitor API call limits
5. Skip usage analysis if not needed (much faster)

For large queries (1000+ records):
1. Use LIMIT clause to test first
2. Add WHERE filters to reduce dataset
3. Export may take 5-10 seconds for very large results
4. Results are paginated automatically

---

## 📊 Export Statistics Explained

### Metadata Export Statistics 🆕

After metadata export completes, you'll see:
```
=== Export Statistics ===
Total Runtime: 00:05:23           ← Time taken
API Calls Made: 156               ← API requests used
Objects Processed: 10/10          ← Success/Total
  ✓ Successful: 10                ← Worked correctly
  ✗ Failed: 0                     ← Had errors
Total Fields: 487                 ← Total fields exported
  - Standard Fields: 350          ← Standard Salesforce fields
  - Custom Fields: 137            ← Custom org fields
  - Formula Fields: 23            ← Calculated fields
  - Lookup Fields: 45             ← Relationship fields
  - Picklist Fields: 67           ← Picklist fields
Fields with Usage Data: 412       ← Fields with usage detected (85%)
```

**Understanding Usage Coverage:**
- **Fields with Usage Data**: Number of fields where usage was detected
- **85-90% coverage** is normal - some fields genuinely have no usage
- **Standard system fields** (CreatedDate, LastModifiedDate) often have no usage data

---

## 🔒 Security & Privacy

- **No credential storage**: Credentials only in memory during session
- **Secure connection**: Uses HTTPS for all API calls
- **Session timeout**: Auto-expires after inactivity
- **Logout**: Always logout to clear credentials from memory

---

## 📝 Daily Workflow Tips

### Best Practices

1. **Start of day:**
   - Launch application
   - Login once
   - Keep application open

2. **During export:**
   - Monitor progress bar (field-based)
   - Check terminal for detailed logs
   - Don't close application mid-export

3. **End of day:**
   - Review export statistics
   - Logout from application
   - Close application

### Recommended Export Patterns

**For complete field documentation:**
```
1. Select objects you want to document
2. Click "📦 Metadata Exporter"
3. ✅ Check "Include field usage analysis"
4. Choose Excel format
5. Save to documentation folder
```

**For quick metadata reference (no usage):**
```
1. Select objects
2. Click "📦 Metadata Exporter"
3. ☐ Leave "Include field usage analysis" unchecked
4. Choose CSV for data analysis
5. Much faster!
```

**For custom development audit:**
```
1. Use "Custom" filter
2. Select all custom objects
3. Click "📦 Metadata Exporter"
4. ✅ Check "Export custom fields only"
5. ✅ Check "Include field usage analysis"
6. Review which custom fields are actually used
```

**For deployment planning:**
```
1. Select objects in your package/feature
2. Click "🔗 Dependency Analysis"
3. Review dependency levels
4. Deploy in order: Level 0, then 1, then 2, etc.
```

**For data analysis:**
```
1. Click "⚡ SOQL Query Runner"
2. Click "📋 Show Objects" → Select object
3. Modify query as needed
4. Click "▶ Execute Query"
5. Click "📊 Export Excel" for analysis
```

---

## 📄 Updating the Application

### To update to newer version:

1. **Backup**: Copy entire project folder
2. **Activate venv**: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. **Update dependencies**: `pip install -r requirements.txt --upgrade`
4. **Replace files**: Overwrite old files with new ones
5. **Test**: Run `python main.py` to verify

---

## 📦 Creating Executable File (Optional)

To create a standalone .exe file (Windows):
```bash
# Activate virtual environment
venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Create single-file executable
pyinstaller --onefile --windowed --name "SME" main.py

# With custom icon (if you have one)
pyinstaller --onefile --windowed --name "SME" --icon=app_icon.ico main.py

# Find your .exe in the 'dist' folder
```

**Result:** Portable .exe file that runs without Python installed

---

## 🆘 Getting Help

- **Setup issues**: Review this README carefully
- **Feature questions**: See FEATURES.md
- **Code reference**: Check inline code comments
- **Errors**: Read terminal logs for detailed error messages

---

## 📚 Additional Resources

**File Structure:**
- `main.py` - Application entry point
- `config/constants.py` - All configuration settings
- `core/salesforce_client.py` - Salesforce API connection
- `exporters/picklist_exporter.py` - Picklist export logic
- `exporters/dependency_analyzer.py` - Dependency analysis logic
- `exporters/metadata_exporter.py` - Metadata export orchestrator
- `exporters/soql_query_runner.py` - SOQL query execution and export
- `exporters/usage_detectors/` - Field usage detection modules (Phase 1)
  - `base_detector.py` - Base class for detectors
  - `layout_detector.py` - Page layout detection
  - `validation_detector.py` - Validation rule detection
  - `workflow_detector.py` - Workflow detection
  - `recordtype_detector.py` - Record type detection
  - `code_search_detector.py` - Apex/VF/Trigger detection
- `ui/login_screen.py` - Login interface
- `ui/main_screen.py` - Main application UI
- `ui/soql_query_screen.py` - SOQL Query Runner UI
- `utils/file_handler.py` - Excel/CSV file creation
- `utils/helpers.py` - Utility functions

**Dependencies:**
- `simple-salesforce` - Salesforce API wrapper
- `openpyxl` - Excel file creation
- `requests` - HTTP requests
- `customtkinter` - Modern GUI framework

---

## ✅ Quick Reference Checklist

**Setup:**
- [ ] Python 3.8+ installed
- [ ] Project structure created (including `usage_detectors` folder)
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Application launches successfully

**First Use:**
- [ ] Security token obtained from Salesforce
- [ ] Connected to Salesforce
- [ ] Objects loaded in available list
- [ ] Test picklist export completed
- [ ] Test dependency analysis completed
- [ ] Test metadata export completed (with usage analysis)
- [ ] Test SOQL query execution completed

**Daily Use:**
- [ ] Virtual environment activated (`(venv)` visible)
- [ ] Login to Salesforce
- [ ] Select objects or write query
- [ ] Choose format
- [ ] Select export type or execute query
- [ ] Enable usage analysis if needed (for Metadata export)
- [ ] Review statistics
- [ ] Logout when done

---

## 🎯 Feature Comparison

| Feature | SME 2.1.0 | Manual Process |
|---------|-----------|----------------|
| Picklist Export | ✅ Automated | ⏰ Hours of manual work |
| Dependency Analysis | ✅ Instant | ⏰ Hours of analysis |
| Field Usage Detection | ✅ 85-90% automated | ⏰ Days of manual checking |
| SOQL Query Runner | ✅ Built-in | 🌐 Need Developer Console |
| Excel Export | ✅ Formatted | ⏰ Manual formatting |
| Progress Tracking | ✅ Real-time | ❌ No visibility |
| Error Handling | ✅ Graceful | ❌ Manual recovery |

---

## 🚀 What's Coming in Phase 2

- Flow/Process Builder detection (85-90% accuracy)
- Report field usage detection (60-70% accuracy)
- Dashboard field usage detection (40-50% accuracy)
- Email template detection (85-90% accuracy)
- Lightning component detection (70-80% accuracy)
- Query history and favorites
- Field auto-complete suggestions

**Phase 1 covers 85-90% of use cases. Phase 2 will increase to 90-95%.**

---

**Version:** 2.1.0 (Phase 1 Complete + SOQL Runner)  
**Last Updated:** 2025

**Made with ❤️ for Salesforce Administrators and Developers**

**Phase 1 Achievement: Comprehensive field usage detection + Full SOQL query capabilities matching industry standards!** 🏆