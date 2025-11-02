# Salesforce Metadata Exporter (SME)

**Version:** 2.0.0  
**A modern GUI application for exporting Salesforce metadata with ease**

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

# Create __init__.py files (makes directories Python packages)
New-Item -ItemType File -Path "config\__init__.py", "core\__init__.py", "exporters\__init__.py", "ui\__init__.py", "utils\__init__.py"
```

**Mac/Linux:**
```bash
# Create project directory and subdirectories
mkdir -p salesforce-metadata-exporter/{config,core,exporters,ui,utils}
cd salesforce-metadata-exporter

# Create __init__.py files
touch config/__init__.py core/__init__.py exporters/__init__.py ui/__init__.py utils/__init__.py
```

---

### 3. Add Project Files

Copy these files to their respective directories:

```
salesforce-metadata-exporter/
├── main.py                          ← Entry point
├── requirements.txt                 ← Dependencies
├── README.md                        ← This file
├── FEATURES.md                      ← Feature documentation
│
├── config/
│   ├── __init__.py
│   └── constants.py                 ← Configuration
│
├── core/
│   ├── __init__.py
│   └── salesforce_client.py         ← Salesforce API
│
├── exporters/
│   ├── __init__.py
│   └── picklist_exporter.py         ← Export logic
│
├── ui/
│   ├── __init__.py
│   ├── login_screen.py              ← Login UI
│   └── main_screen.py               ← Main UI
│
└── utils/
    ├── __init__.py
    ├── file_handler.py              ← File operations
    └── helpers.py                   ← Utilities
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

## 🔑 Getting Started - First Use

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

---

## 🎯 Using the Application

### 1. Export Picklist Data (Step-by-Step)

1. **Wait for objects to load** (30-60 seconds for large orgs)

2. **Find objects:**
   - Use **filters**: All / Standard / Custom
   - Or **search**: Type object name in search box
   - Example: Type "Account" to find Account object

3. **Select objects:**
   - Click object in "Available Objects" list
   - Click **"Add >>"** button
   - Or click **"Select All"** to add all filtered objects
   - Selected objects appear in "Selected Objects" list

4. **Remove objects (optional):**
   - Click object in "Selected Objects" list
   - Click **"<< Remove"** button
   - Or click **"Deselect All"** to remove all

5. **Choose export format:**
   - Select **Excel (.xlsx)** or **CSV (.csv)** radio button

6. **Start export:**
   - Click **"📋 Export Picklist Data"** button
   - Choose save location and filename
   - Click **Save**

7. **Monitor progress:**
   - Progress bar shows completion percentage
   - Terminal shows detailed processing logs
   - Status bar shows current operation
   - You can click **"❌ Cancel Export"** to stop

8. **Review results:**
   - Success message appears when complete
   - Check terminal for statistics:
     - Total runtime
     - Objects processed
     - API calls made
     - Fields found
     - Values exported

### 2. Dependency Analysis (Step-by-Step)

**Analyze relationships between Salesforce objects to determine deployment order.**

1. **Select objects to analyze:**
   - Select **at least 2 objects** from available list
   - Click **"Add >>"** to move to selected objects
   - Example: Select Account, Contact, Opportunity

2. **Start analysis:**
   - Click **"🔗 Dependency Analysis"** button
   - Choose save location and filename
   - Click **Save**

3. **Choose export format:**
   - Select **Excel (.xlsx)** or **CSV (.csv)** radio button

4. **Monitor progress:**
   - Progress bar shows percentage
   - Terminal shows detailed analysis logs
   - Status bar shows current object being analyzed
   - You can click **"⏸️ Cancel Analysis"** to stop

5. **Review results:**
   - Success message appears when complete
   - Check terminal for statistics:
     - Total runtime
     - Objects analyzed
     - API calls made
     - Dependencies found (Lookup/Master-Detail)
     - Maximum dependency level
     - External dependencies ignored

### Dependency Analysis Output Format

**Columns in exported file:**
| Column | Description |
|--------|-------------|
| Object API Name | Object being analyzed (e.g., Contact) |
| Dependent Object API Names | Objects this depends on (e.g., Account) |
| Dependency Level | Deployment order (0 = deploy first, 1+ = depends on lower levels) |

**Example Output:**
| Object API Name | Dependent Object API Names | Dependency Level |
|-----------------|---------------------------|------------------|
| Account | - | 0 |
| Lead | - | 0 |
| Contact | Account | 1 |
| Opportunity | Account(Contact) | 2 |

**Reading the Output:**
- **Level 0**: No dependencies, deploy first
- **Level 1**: Depends on Level 0 objects
- **Level 2**: Depends on Level 0 and/or Level 1 objects
- **Required**: Master-Detail relationship (must exist)
- **(Optional)**: Lookup relationship (can be null)
- **↻**: Self-reference (object references itself)

**Deployment Order:**
Simply deploy from top to bottom! Objects are sorted by level, then alphabetically.

### Dependency Analysis Features
- ✅ **Isolated Analysis**: Only shows dependencies between selected objects
- ✅ **Ignores External Dependencies**: Filters out non-selected object dependencies
- ✅ **Relationship Types**: Identifies Lookup, Master-Detail, and Junction relationships
- ✅ **Self-References**: Detects when objects reference themselves
- ✅ **Deployment Levels**: Calculates optimal deployment order
- ✅ **Sorted Output**: Ordered by level first, then alphabetically

### Export Picklist Data Output Format

**Columns in exported file:**
| Column | Description |
|--------|-------------|
| Object | Object API name (e.g., Account) |
| Field Label | User-friendly field name (e.g., Industry) |
| Field API Name | API name (e.g., Industry) |
| Picklist Value Label | Display value (e.g., Technology) |
| Picklist Value API Name | API value (e.g., Technology) |
| Status | Active or Inactive |

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **F11** | Toggle fullscreen mode |
| **Escape** | Exit fullscreen |
| **Enter** | Submit login (when on login screen) |

---

## 🎨 Application Features

### Current Features
- ✅ **Picklist Data Export**: Export all picklist values (active/inactive) from any object
- ✅ **Dependency Analysis**: Analyze object relationships and determine deployment order
- ✅ **Isolated Analysis**: Shows only dependencies between selected objects (no external noise)
- ✅ **Multiple Export Formats**: Excel (.xlsx) and CSV (.csv)
- ✅ **Real-time Progress**: Live updates during export/analysis
- ✅ **Theme Toggle**: Switch between dark/light mode (🌙/☀️)
- ✅ **Smart Filters**: Filter by All/Standard/Custom objects
- ✅ **Instant Search**: Find objects quickly
- ✅ **Cancel Support**: Stop operations anytime
- ✅ **Detailed Statistics**: Comprehensive export/analysis summaries

### UI Features
- ✅ **Theme Toggle**: Switch between dark/light mode (🌙/☀️ button)
- ✅ **Resizable Window**: Drag edges to resize
- ✅ **Fullscreen Mode**: Press F11 for distraction-free mode
- ✅ **Centered Launch**: Always opens in screen center
- ✅ **Real-time Progress**: Live updates during export

### Object Selection
- ✅ **Smart Filters**: All / Standard / Custom objects
- ✅ **Instant Search**: Find objects quickly
- ✅ **Bulk Operations**: Select All / Deselect All
- ✅ **Visual Feedback**: Selected objects highlighted
- ✅ **Count Display**: Shows number of objects in each list

### Export Features
- ✅ **Multiple Formats**: Excel or CSV
- ✅ **Auto-splitting**: Handles large datasets
  - Excel: Splits at 1,048,576 rows
  - CSV: Splits at 1,000,000 rows
- ✅ **Professional Formatting**: Excel headers styled
- ✅ **Cancel Support**: Stop export anytime
- ✅ **Statistics**: Detailed export summary

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

**If "No module named 'config'" error:**
- Ensure `__init__.py` files exist in all directories
- Check you're in the correct directory

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
- 🔑 **Permissions**: Verify API access in Salesforce profile

### Export fails
- ❌ Object doesn't exist in org
- ❌ No picklist fields in selected object (for picklist export)
- ❌ Less than 2 objects selected (for dependency analysis)
- ❌ API limit reached (check daily limits)
- 📋 Review terminal logs for specific error

### Dependency Analysis specific issues
- ❌ **"Requires at least 2 objects"**: Select 2+ objects before clicking
- ❌ **No dependencies found**: Selected objects don't reference each other
- ❌ **External dependencies ignored**: Normal behavior - only shows internal relationships
- 📋 Check terminal logs to see ignored external dependencies

### Performance issues
For large orgs (500+ objects):
1. Use filters (Standard/Custom) to reduce list size
2. Search for specific objects instead of scrolling
3. Export in smaller batches
4. Monitor API call limits

---

## 📊 Export Statistics Explained

### Picklist Export Statistics

After picklist export completes, you'll see:

```
=== Export Statistics ===
Total Runtime: 00:02:45           ← Time taken
API Calls Made: 12                ← API requests used
Objects Processed: 5/5            ← Success/Total
  ✓ Successful: 5                 ← Worked correctly
  ✗ Failed: 0                     ← Had errors
Total Picklist Fields: 18         ← Fields found
Total Picklist Values: 156        ← Values exported
  - Active: 142                   ← Currently active
  - Inactive: 14                  ← Deprecated values
```

### Dependency Analysis Statistics

After dependency analysis completes, you'll see:

```
=== Dependency Analysis Statistics ===
Total Runtime: 00:00:45           ← Time taken
API Calls Made: 15                ← API requests used
Objects Analyzed: 15/15           ← Success/Total
  ✓ Successful: 15                ← Analyzed correctly
  ✗ Failed: 0                     ← Had errors
Total Dependencies Found: 23      ← Total relationships
  - Lookup: 12                    ← Optional relationships
  - Master-Detail: 11             ← Required relationships
  - Self-References: 2            ← Self-referencing objects
External Dependencies Ignored: 8  ← Non-selected objects filtered
Max Dependency Level: 4           ← Deepest deployment level
```

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
   - Monitor progress bar
   - Check terminal for issues
   - Don't close application mid-export

3. **End of day:**
   - Review export statistics
   - Logout from application
   - Close application

### Recommended Export Patterns

**For picklist metadata backup:**
```
1. Select "All" filter
2. Click "Select All"
3. Choose Excel format
4. Export to dated folder (e.g., Backup_2024-01-15/)
```

**For specific analysis:**
```
1. Use Custom/Standard filter
2. Search for specific objects
3. Select relevant objects only
4. Choose CSV for data analysis tools
```

**For dependency analysis:**
```
1. Select objects you want to analyze as a group
2. Use Custom filter for custom objects only
3. Choose Excel for formatted output
4. Export to deployment planning folder
5. Use output to plan deployment order
```

**For deployment planning:**
```
1. Select all objects in your package/feature
2. Run Dependency Analysis
3. Review dependency levels in output
4. Deploy objects level by level (0, then 1, then 2, etc.)
```

---

## 🔄 Updating the Application

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
- `ui/login_screen.py` - Login interface
- `ui/main_screen.py` - Main application UI
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
- [ ] Project structure created
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Application launches successfully

**First Use:**
- [ ] Security token obtained from Salesforce
- [ ] Connected to Salesforce
- [ ] Objects loaded in available list
- [ ] Test picklist export completed successfully
- [ ] Test dependency analysis completed successfully (with 2+ objects)

**Daily Use:**
- [ ] Virtual environment activated (`(venv)` visible)
- [ ] Login to Salesforce
- [ ] Select objects
- [ ] Choose format
- [ ] Export picklist data OR run dependency analysis
- [ ] Review statistics
- [ ] Logout when done

---

**Version:** 2.0.0  
**Last Updated:** 2025

**Made with ❤️ for Salesforce Administrators and Developers**