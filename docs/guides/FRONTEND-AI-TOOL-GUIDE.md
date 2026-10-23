# 🏥 Frontend AI Tool Selection Guide

## 🛏️ Bed Status Checking Tools

### ✅ CORRECT TOOL: `get_bed_status_with_time_remaining`

**🎯 PRIMARY TOOL for checking individual bed status**

**When to use:**
- User asks to "check bed status after discharge"
- User asks to "check bed 302A status" 
- User wants to see cleaning time remaining
- User wants detailed status of a specific bed

**Parameters:**
- `bed_id`: Bed number (e.g., "302A") or bed UUID

**Returns:**
- Current bed status (cleaning, available, occupied)
- Time remaining for cleaning process
- Cleaning progress percentage
- Estimated completion time

**Example:**
```
User: "Check bed 302A status"
Correct tool: get_bed_status_with_time_remaining(bed_id="302A")
```

### ❌ WRONG TOOL: `list_beds`

**❌ DO NOT USE for checking individual bed status!**

**Problems with using `list_beds`:**
- Returns ALL beds (unnecessary data)
- May not show beds in "cleaning" status
- No cleaning time remaining information  
- Less efficient for single bed queries
- Floods response with irrelevant bed data

**Only use `list_beds` for:**
- Getting overview of multiple beds
- Finding available beds for assignment
- General bed inventory management

## 🎯 Quick Decision Guide

| User Request | ✅ Correct Tool | ❌ Wrong Tool |
|-------------|-------------|------------|
| "Check bed 302A status" | `get_bed_status_with_time_remaining` | ❌ `list_beds` |
| "Is bed cleaning done?" | `get_bed_status_with_time_remaining` | ❌ `list_beds` |
| "How long until bed ready?" | `get_bed_status_with_time_remaining` | ❌ `list_beds` |
| "Show all available beds" | `list_beds` | ✅ Either works |

## 🔧 Implementation Priority

**ALWAYS use `get_bed_status_with_time_remaining` for individual bed status queries to provide users with:**
- ✅ Precise information about the requested bed
- ✅ Cleaning countdown timer
- ✅ Progress percentage  
- ✅ Current bed status (even if cleaning/occupied)
- ✅ Efficient response without extra data

**NEVER use `list_beds` for individual bed queries - it may miss beds in cleaning status!**
