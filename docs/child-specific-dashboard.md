# Child-Specific Dashboard Implementation

## Overview

The Chuopay system implements a **child-specific dashboard** approach where parents first select a child, and then the dashboard shows data exclusively for that selected child. This provides a clean, focused experience without combined views.

## Key Features

### 🎯 **Child Selection First**

- Parents must select a child before accessing dashboard
- No combined views of multiple children
- Each child has their own isolated dashboard

### 🔄 **Easy Child Switching**

- Parents can switch between children
- Dashboard refreshes completely for each child
- No data mixing between children

### 📊 **Child-Specific Data**

- All statistics are calculated per child
- Events are filtered by child's groups
- Contributions are isolated per child

## API Endpoints

### 1. **Get All Children**

```http
GET /api/parent-dashboard/my_children/
```

**Response:**

```json
[
  {
    "id": 1,
    "first_name": "Alice",
    "last_name": "Johnson",
    "full_name": "Alice Johnson",
    "student_id": "STU001",
    "section": {
      "id": 1,
      "display_name": "Primary School"
    },
    "school": {
      "id": 1,
      "name": "Test School"
    }
  },
  {
    "id": 2,
    "first_name": "Bob",
    "last_name": "Smith",
    "full_name": "Bob Smith",
    "student_id": "STU002",
    "section": {
      "id": 1,
      "display_name": "Primary School"
    },
    "school": {
      "id": 1,
      "name": "Test School"
    }
  }
]
```

### 2. **Child-Specific Dashboard**

```http
GET /api/parent-dashboard/child_dashboard/?child_id=1
```

**Response:**

```json
{
  "child": {
    "id": 1,
    "first_name": "Alice",
    "last_name": "Johnson",
    "full_name": "Alice Johnson",
    "student_id": "STU001",
    "section": {
      "id": 1,
      "display_name": "Primary School"
    }
  },
  "groups": [
    {
      "id": 1,
      "name": "Class 1A",
      "section": {
        "id": 1,
        "display_name": "Primary School"
      }
    }
  ],
  "statistics": {
    "total_contributions": 5,
    "paid_contributions": 3,
    "pending_contributions": 2,
    "total_amount_paid": 15000.0,
    "payment_percentage": 60.0
  },
  "upcoming_events": [
    {
      "id": 1,
      "name": "Field Trip",
      "due_date": "2024-02-15T10:00:00Z",
      "amount": 5000.0
    }
  ],
  "recent_contributions": [
    {
      "id": 1,
      "event": {
        "name": "School Uniform"
      },
      "amount_required": 3000.0,
      "amount_paid": 3000.0,
      "payment_status": "paid"
    }
  ]
}
```

### 3. **Child-Specific Events**

```http
GET /api/parent-dashboard/child_events/?child_id=1
```

### 4. **Child-Specific Contributions**

```http
GET /api/parent-dashboard/child_contributions/?child_id=1
```

### 5. **Child-Specific Groups**

```http
GET /api/parent-dashboard/child_groups/?child_id=1
```

## UI Flow Implementation

### **Step 1: Parent Login**

```javascript
// After successful login, redirect to child selection
if (user.role === "parent") {
  router.push("/select-child");
}
```

### **Step 2: Child Selection Screen**

```javascript
// Fetch all children for the parent
const fetchChildren = async () => {
  const response = await fetch("/api/parent-dashboard/my_children/");
  const children = await response.json();
  setChildren(children);
};

// Child selection component
const ChildSelection = ({ children, onChildSelect }) => {
  return (
    <div className="child-selection">
      <h2>Select a Child</h2>
      <div className="children-grid">
        {children.map((child) => (
          <div
            key={child.id}
            className="child-card"
            onClick={() => onChildSelect(child.id)}
          >
            <h3>{child.full_name}</h3>
            <p>{child.section.display_name}</p>
            <p>Student ID: {child.student_id}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### **Step 3: Dashboard for Selected Child**

```javascript
// Store selected child in state/localStorage
const [selectedChildId, setSelectedChildId] = useState(null);

const onChildSelect = (childId) => {
  setSelectedChildId(childId);
  localStorage.setItem("selectedChildId", childId);
  router.push(`/dashboard?child_id=${childId}`);
};

// Dashboard component
const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const { child_id } = useSearchParams();

  const fetchDashboardData = async () => {
    const response = await fetch(
      `/api/parent-dashboard/child_dashboard/?child_id=${child_id}`
    );
    const data = await response.json();
    setDashboardData(data);
  };

  useEffect(() => {
    if (child_id) {
      fetchDashboardData();
    }
  }, [child_id]);

  return (
    <div className="dashboard">
      <ChildHeader child={dashboardData?.child} />
      <Statistics stats={dashboardData?.statistics} />
      <UpcomingEvents events={dashboardData?.upcoming_events} />
      <RecentContributions
        contributions={dashboardData?.recent_contributions}
      />
    </div>
  );
};
```

### **Step 4: Child Switching**

```javascript
// Child switcher component
const ChildSwitcher = ({ children, selectedChildId, onChildSwitch }) => {
  return (
    <div className="child-switcher">
      <select
        value={selectedChildId}
        onChange={(e) => onChildSwitch(e.target.value)}
      >
        {children.map((child) => (
          <option key={child.id} value={child.id}>
            {child.full_name}
          </option>
        ))}
      </select>
    </div>
  );
};

const onChildSwitch = (childId) => {
  setSelectedChildId(childId);
  localStorage.setItem("selectedChildId", childId);
  router.push(`/dashboard?child_id=${childId}`);
  // Dashboard will re-fetch data for new child
};
```

## URL Structure

### **Child Selection**

```
/select-child
```

### **Dashboard**

```
/dashboard?child_id=1
```

### **Child-Specific Pages**

```
/events?child_id=1
/contributions?child_id=1
/groups?child_id=1
/payments?child_id=1
```

## Data Isolation

### **Complete Child Isolation**

- Each child's data is completely separate
- No shared statistics between children
- Events are filtered by child's specific groups
- Contributions are isolated per child

### **Example Data Flow**

```
Parent with 2 children:
├── Alice Johnson (Primary)
│   ├── Groups: Class 1A
│   ├── Events: Field Trip, Uniform
│   └── Contributions: 3 paid, 1 pending
└── Bob Smith (Primary)
    ├── Groups: Class 1A
    ├── Events: Field Trip, Uniform
    └── Contributions: 2 paid, 2 pending

When viewing Alice's dashboard:
✅ Shows only Alice's data
✅ Statistics: 3 paid, 1 pending
✅ Events: Only events for Class 1A
❌ No data from Bob Smith

When switching to Bob's dashboard:
✅ Shows only Bob's data
✅ Statistics: 2 paid, 2 pending
✅ Events: Only events for Class 1A
❌ No data from Alice Johnson
```

## Benefits

### **1. Clean User Experience**

- No confusion about which child's data is being viewed
- Clear, focused dashboard for each child
- Easy to understand and navigate

### **2. Data Security**

- Complete isolation between children
- Parents can't accidentally mix data
- Clear audit trail per child

### **3. Performance**

- Smaller data sets per request
- Faster loading times
- Reduced memory usage

### **4. Scalability**

- Works for parents with many children
- Each child's data is independent
- Easy to add new children

## Implementation Notes

### **State Management**

```javascript
// Store selected child in localStorage for persistence
localStorage.setItem("selectedChildId", childId);

// Retrieve on app load
const savedChildId = localStorage.getItem("selectedChildId");
if (savedChildId) {
  setSelectedChildId(savedChildId);
}
```

### **Error Handling**

```javascript
// Handle child not found
if (!child) {
  return <ErrorComponent message="Child not found or access denied" />;
}

// Handle no children
if (children.length === 0) {
  return <NoChildrenComponent />;
}
```

### **Loading States**

```javascript
const [isLoading, setIsLoading] = useState(false);

const fetchDashboardData = async () => {
  setIsLoading(true);
  try {
    const data = await fetch(
      `/api/parent-dashboard/child_dashboard/?child_id=${childId}`
    );
    setDashboardData(data);
  } finally {
    setIsLoading(false);
  }
};
```

## Testing

Use the provided test script to verify functionality:

```bash
python test_child_dashboard.py
```

This script demonstrates:

- Child selection functionality
- Data isolation between children
- API endpoint behavior
- UI flow simulation

## Conclusion

The child-specific dashboard approach provides a clean, secure, and user-friendly experience for parents managing multiple children. Each child has their own isolated dashboard, making it easy to focus on individual needs while maintaining clear data separation.
