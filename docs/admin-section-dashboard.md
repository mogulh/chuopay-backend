# Admin Section-Specific Dashboard Implementation

## Overview

The Chuopay system implements a **section-specific dashboard** approach for administrators where they first select a section, and then the dashboard shows data exclusively for that selected section. This provides focused management capabilities for multi-section schools.

## Key Features

### 🎯 **Section Selection First**

- Administrators must select a section before accessing dashboard
- No combined views of multiple sections
- Each section has its own isolated dashboard

### 🔄 **Easy Section Switching**

- Administrators can switch between sections
- Dashboard refreshes completely for each section
- No data mixing between sections

### 📊 **Section-Specific Data**

- All statistics are calculated per section
- Students, groups, events are filtered by section
- Analytics are isolated per section

## API Endpoints

### 1. **Get All Sections**

```http
GET /api/admin-dashboard/my_sections/
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "primary",
    "display_name": "Primary School",
    "description": "Primary school section",
    "is_active": true,
    "section_head": {
      "id": 2,
      "full_name": "John Teacher"
    },
    "school": {
      "id": 1,
      "name": "Test School"
    },
    "groups_count": 3,
    "students_count": 45
  },
  {
    "id": 2,
    "name": "secondary",
    "display_name": "Secondary School",
    "description": "Secondary school section",
    "is_active": true,
    "section_head": null,
    "school": {
      "id": 1,
      "name": "Test School"
    },
    "groups_count": 2,
    "students_count": 32
  }
]
```

### 2. **Section-Specific Dashboard**

```http
GET /api/admin-dashboard/section_dashboard/?section_id=1
```

**Response:**

```json
{
  "section": {
    "id": 1,
    "name": "primary",
    "display_name": "Primary School",
    "description": "Primary school section",
    "is_active": true
  },
  "statistics": {
    "total_students": 45,
    "active_students": 42,
    "inactive_students": 3,
    "total_groups": 3,
    "total_events": 8,
    "active_events": 5,
    "total_contributions": 156,
    "paid_contributions": 142,
    "pending_contributions": 14,
    "total_amount_paid": 450000.0,
    "total_amount_required": 480000.0,
    "payment_percentage": 91.0,
    "collection_rate": 93.75
  },
  "recent_events": [
    {
      "id": 1,
      "name": "Field Trip",
      "due_date": "2024-02-15T10:00:00Z",
      "amount": 5000.0,
      "is_active": true,
      "is_published": true
    }
  ],
  "recent_contributions": [
    {
      "id": 1,
      "student": {
        "full_name": "Alice Johnson"
      },
      "event": {
        "name": "School Uniform"
      },
      "amount_required": 3000.0,
      "amount_paid": 3000.0,
      "payment_status": "paid"
    }
  ],
  "top_groups": [
    {
      "id": 1,
      "name": "Class 1A",
      "student_count": 15,
      "contribution_count": 45
    }
  ]
}
```

### 3. **Section-Specific Students**

```http
GET /api/admin-dashboard/section_students/?section_id=1
```

### 4. **Section-Specific Groups**

```http
GET /api/admin-dashboard/section_groups/?section_id=1
```

### 5. **Section-Specific Events**

```http
GET /api/admin-dashboard/section_events/?section_id=1
```

### 6. **Section-Specific Contributions**

```http
GET /api/admin-dashboard/section_contributions/?section_id=1
```

### 7. **Section-Specific Analytics**

```http
GET /api/admin-dashboard/section_analytics/?section_id=1
```

**Response:**

```json
{
  "section": {
    "id": 1,
    "display_name": "Primary School"
  },
  "monthly_trends": [
    {
      "month": "2024-01-01T00:00:00Z",
      "total_amount": 150000.0,
      "count": 45
    },
    {
      "month": "2024-02-01T00:00:00Z",
      "total_amount": 180000.0,
      "count": 52
    }
  ],
  "payment_methods": [
    {
      "payment_method": "mpesa",
      "count": 120,
      "total_amount": 360000.0
    },
    {
      "payment_method": "bank_transfer",
      "count": 36,
      "total_amount": 90000.0
    }
  ],
  "event_performance": [
    {
      "id": 1,
      "name": "School Uniform",
      "total_contributions": 45,
      "paid_contributions": 42,
      "total_amount": 126000.0
    }
  ]
}
```

## UI Flow Implementation

### **Step 1: Admin Login**

```javascript
// After successful login, redirect to section selection
if (user.role === "admin") {
  router.push("/select-section");
}
```

### **Step 2: Section Selection Screen**

```javascript
// Fetch all sections for the admin
const fetchSections = async () => {
  const response = await fetch("/api/admin-dashboard/my_sections/");
  const sections = await response.json();
  setSections(sections);
};

// Section selection component
const SectionSelection = ({ sections, onSectionSelect }) => {
  return (
    <div className="section-selection">
      <h2>Select a Section</h2>
      <div className="sections-grid">
        {sections.map((section) => (
          <div
            key={section.id}
            className="section-card"
            onClick={() => onSectionSelect(section.id)}
          >
            <h3>{section.display_name}</h3>
            <p>{section.description}</p>
            <div className="section-stats">
              <span>{section.groups_count} Groups</span>
              <span>{section.students_count} Students</span>
            </div>
            {section.section_head && (
              <p>Head: {section.section_head.full_name}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### **Step 3: Dashboard for Selected Section**

```javascript
// Store selected section in state/localStorage
const [selectedSectionId, setSelectedSectionId] = useState(null);

const onSectionSelect = (sectionId) => {
  setSelectedSectionId(sectionId);
  localStorage.setItem("selectedSectionId", sectionId);
  router.push(`/dashboard?section_id=${sectionId}`);
};

// Dashboard component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const { section_id } = useSearchParams();

  const fetchDashboardData = async () => {
    const response = await fetch(
      `/api/admin-dashboard/section_dashboard/?section_id=${section_id}`
    );
    const data = await response.json();
    setDashboardData(data);
  };

  useEffect(() => {
    if (section_id) {
      fetchDashboardData();
    }
  }, [section_id]);

  return (
    <div className="dashboard">
      <SectionHeader section={dashboardData?.section} />
      <Statistics stats={dashboardData?.statistics} />
      <RecentEvents events={dashboardData?.recent_events} />
      <RecentContributions
        contributions={dashboardData?.recent_contributions}
      />
      <TopGroups groups={dashboardData?.top_groups} />
    </div>
  );
};
```

### **Step 4: Section Switching**

```javascript
// Section switcher component
const SectionSwitcher = ({ sections, selectedSectionId, onSectionSwitch }) => {
  return (
    <div className="section-switcher">
      <select
        value={selectedSectionId}
        onChange={(e) => onSectionSwitch(e.target.value)}
      >
        {sections.map((section) => (
          <option key={section.id} value={section.id}>
            {section.display_name}
          </option>
        ))}
      </select>
    </div>
  );
};

const onSectionSwitch = (sectionId) => {
  setSelectedSectionId(sectionId);
  localStorage.setItem("selectedSectionId", sectionId);
  router.push(`/dashboard?section_id=${sectionId}`);
  // Dashboard will re-fetch data for new section
};
```

## URL Structure

### **Section Selection**

```
/select-section
```

### **Dashboard**

```
/dashboard?section_id=1
```

### **Section-Specific Pages**

```
/students?section_id=1
/groups?section_id=1
/events?section_id=1
/contributions?section_id=1
/analytics?section_id=1
```

## Data Isolation

### **Complete Section Isolation**

- Each section's data is completely separate
- No shared statistics between sections
- Students, groups, events are filtered by section
- Analytics are isolated per section

### **Example Data Flow**

```
School with 2 sections:
├── Primary School
│   ├── Students: 45 students
│   ├── Groups: 3 groups
│   ├── Events: 8 events
│   └── Contributions: 156 contributions
└── Secondary School
    ├── Students: 32 students
    ├── Groups: 2 groups
    ├── Events: 5 events
    └── Contributions: 98 contributions

When viewing Primary School dashboard:
✅ Shows only Primary School data
✅ Statistics: 45 students, 3 groups, 8 events
✅ Students: Only Primary School students
❌ No data from Secondary School

When switching to Secondary School dashboard:
✅ Shows only Secondary School data
✅ Statistics: 32 students, 2 groups, 5 events
✅ Students: Only Secondary School students
❌ No data from Primary School
```

## Benefits

### **1. Focused Management**

- Clear view of each section's performance
- Easy to identify section-specific issues
- Targeted management strategies

### **2. Data Security**

- Complete isolation between sections
- Section-specific access control
- Clear audit trail per section

### **3. Performance**

- Smaller, focused data sets
- Faster loading times
- Reduced memory usage

### **4. Scalability**

- Works for schools with many sections
- Each section's data is independent
- Easy to add new sections

### **5. Analytics**

- Section-specific performance metrics
- Comparative analysis between sections
- Targeted improvement strategies

## Implementation Notes

### **State Management**

```javascript
// Store selected section in localStorage for persistence
localStorage.setItem("selectedSectionId", sectionId);

// Retrieve on app load
const savedSectionId = localStorage.getItem("selectedSectionId");
if (savedSectionId) {
  setSelectedSectionId(savedSectionId);
}
```

### **Error Handling**

```javascript
// Handle section not found
if (!section) {
  return <ErrorComponent message="Section not found or access denied" />;
}

// Handle no sections
if (sections.length === 0) {
  return <NoSectionsComponent />;
}
```

### **Loading States**

```javascript
const [isLoading, setIsLoading] = useState(false);

const fetchDashboardData = async () => {
  setIsLoading(true);
  try {
    const data = await fetch(
      `/api/admin-dashboard/section_dashboard/?section_id=${sectionId}`
    );
    setDashboardData(data);
  } finally {
    setIsLoading(false);
  }
};
```

### **Analytics Integration**

```javascript
// Fetch section-specific analytics
const fetchAnalytics = async (sectionId) => {
  const response = await fetch(
    `/api/admin-dashboard/section_analytics/?section_id=${sectionId}`
  );
  const analytics = await response.json();
  return analytics;
};
```

## Testing

Use the provided test script to verify functionality:

```bash
python test_admin_dashboard.py
```

This script demonstrates:

- Section selection functionality
- Data isolation between sections
- API endpoint behavior
- UI flow simulation
- Analytics data structure

## Comparison with Parent Dashboard

| Feature        | Parent Dashboard     | Admin Dashboard        |
| -------------- | -------------------- | ---------------------- |
| **Selection**  | Child selection      | Section selection      |
| **Data Scope** | Child-specific       | Section-specific       |
| **Statistics** | Per child            | Per section            |
| **Analytics**  | Child performance    | Section performance    |
| **Navigation** | Child-based URLs     | Section-based URLs     |
| **Isolation**  | Child data isolation | Section data isolation |

## Conclusion

The admin section-specific dashboard approach provides focused management capabilities for multi-section schools. Each section has its own isolated dashboard, making it easy to manage section-specific needs while maintaining clear data separation and providing targeted analytics for performance improvement.
