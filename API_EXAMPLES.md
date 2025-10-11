# ThesisLink API Usage Examples

## Complete Workflow Examples

### Example 1: Complete Onboarding & First Email

This example shows a complete workflow from registration to sending your first personalized email.

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Step 1: Register a new user
print("Step 1: Registering user...")
register_response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "grad.student@university.edu",
        "username": "gradstudent",
        "password": "SecurePassword123!",
        "full_name": "Jane Doe"
    }
)
print(f"✓ User registered: {register_response.json()}")

# Step 2: Login to get token
print("\nStep 2: Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "gradstudent",
        "password": "SecurePassword123!"
    }
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✓ Logged in successfully")

# Step 3: Create an email template
print("\nStep 3: Creating email template...")
template_response = requests.post(
    f"{BASE_URL}/templates/",
    headers=headers,
    json={
        "name": "PhD Application Initial Contact",
        "subject": "PhD Application Inquiry - [ResearchTopic]",
        "body": """Dear Professor [ProfName],

I hope this email finds you well. I am writing to express my strong interest in pursuing a PhD in [Department] at [University], specifically to work under your supervision.

I am particularly fascinated by your research on [ResearchInterest]. My background in machine learning and natural language processing aligns well with your current work.

I have attached my CV and statement of purpose for your consideration. I would greatly appreciate the opportunity to discuss potential research opportunities in your group.

Thank you for your time and consideration.

Best regards,
Jane Doe""",
        "is_default": True,
        "use_ai_personalization": True,
        "description": "Template for initial PhD application contact"
    }
)
template_id = template_response.json()["id"]
print(f"✓ Template created with ID: {template_id}")

# Step 4: Add a contact (professor)
print("\nStep 4: Adding professor contact...")
contact_response = requests.post(
    f"{BASE_URL}/contacts/",
    headers=headers,
    json={
        "name": "Dr. John Smith",
        "email": "john.smith@mit.edu",
        "university": "Massachusetts Institute of Technology",
        "department": "Computer Science",
        "research_interest": "Deep Learning, Computer Vision, Neural Architecture Search",
        "website": "https://www.mit.edu/~jsmith",
        "notes": "Published groundbreaking work on NAS in 2023",
        "status": "new"
    }
)
contact_id = contact_response.json()["id"]
print(f"✓ Contact added with ID: {contact_id}")

# Step 5: Personalize template for this contact (preview)
print("\nStep 5: Generating personalized email preview...")
personalize_response = requests.post(
    f"{BASE_URL}/templates/personalize",
    headers=headers,
    params={"use_ai": True},
    json={
        "template_id": template_id,
        "contact_id": contact_id,
        "additional_context": "Mention my recent paper on efficient neural networks"
    }
)
personalized = personalize_response.json()
print(f"\n--- Personalized Email Preview ---")
print(f"Subject: {personalized['subject']}")
print(f"\n{personalized['body']}")
print(f"--- End Preview ---\n")

# Step 6: Send the email
print("Step 6: Sending email...")
send_response = requests.post(
    f"{BASE_URL}/email/send",
    headers=headers,
    json={
        "contact_id": contact_id,
        "template_id": template_id,
        "use_ai": True,
        "additional_context": "Mention my recent paper on efficient neural networks"
    }
)
print(f"✓ Email sent: {send_response.json()['message']}")

# Step 7: Check dashboard stats
print("\nStep 7: Checking dashboard stats...")
stats_response = requests.get(
    f"{BASE_URL}/dashboard/stats",
    headers=headers
)
stats = stats_response.json()
print(f"✓ Dashboard stats:")
print(f"  - Total contacts: {stats['contacts']['total']}")
print(f"  - Emails sent (last 7 days): {stats['activity']['emails_sent_last_7_days']}")
print(f"  - Templates: {stats['resources']['templates']}")

print("\n✓ Complete workflow finished successfully!")
```

### Example 2: Bulk Contact Import & Batch Email

```python
import requests
import csv
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token-here"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Read contacts from CSV
contacts_data = [
    {
        "name": "Dr. Alice Johnson",
        "email": "alice.j@stanford.edu",
        "university": "Stanford University",
        "department": "Computer Science",
        "research_interest": "Natural Language Processing, Transformers"
    },
    {
        "name": "Dr. Bob Williams",
        "email": "bob.w@berkeley.edu",
        "university": "UC Berkeley",
        "department": "EECS",
        "research_interest": "Reinforcement Learning, Robotics"
    },
    {
        "name": "Dr. Carol Davis",
        "email": "carol.d@cmu.edu",
        "university": "Carnegie Mellon University",
        "department": "Machine Learning",
        "research_interest": "Computer Vision, 3D Reconstruction"
    }
]

# Import all contacts
print("Importing contacts...")
contact_ids = []
for contact_data in contacts_data:
    response = requests.post(
        f"{BASE_URL}/contacts/",
        headers=headers,
        json=contact_data
    )
    contact_id = response.json()["id"]
    contact_ids.append(contact_id)
    print(f"✓ Added {contact_data['name']} (ID: {contact_id})")

# Send batch emails with 10-second delay between each
print("\nSending batch emails...")
batch_response = requests.post(
    f"{BASE_URL}/email/batch",
    headers=headers,
    json={
        "contact_ids": contact_ids,
        "template_id": 1,  # Use default template
        "use_ai": True,
        "delay_seconds": 10
    }
)
results = batch_response.json()["results"]
print(f"✓ Sent {results['success']} emails successfully")
print(f"✗ Failed: {results['failed']} emails")
if results['failed_emails']:
    print(f"  Failed emails: {', '.join(results['failed_emails'])}")

print("\n✓ Batch import and email sending complete!")
```

### Example 3: Follow-Up Management

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token-here"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Get all contacted but not replied contacts
print("Finding contacts that need follow-up...")
response = requests.get(
    f"{BASE_URL}/contacts/",
    headers=headers,
    params={"status": "contacted", "page": 1, "page_size": 50}
)
contacted_contacts = response.json()["contacts"]

print(f"Found {len(contacted_contacts)} contacted professors")

# Schedule follow-ups for next week
for contact in contacted_contacts:
    # Check if already followed up recently
    if contact["last_contacted_at"]:
        last_contact = datetime.fromisoformat(contact["last_contacted_at"].replace('Z', '+00:00'))
        days_since = (datetime.now() - last_contact).days
        
        if days_since >= 14:  # Follow up after 2 weeks
            followup_date = datetime.now() + timedelta(days=7)
            
            response = requests.post(
                f"{BASE_URL}/email/schedule-followup",
                headers=headers,
                json={
                    "contact_id": contact["id"],
                    "followup_date": followup_date.isoformat(),
                    "template_id": 2  # Follow-up template
                }
            )
            
            print(f"✓ Scheduled follow-up for {contact['name']} on {followup_date.date()}")

# Check upcoming follow-ups
print("\nChecking upcoming follow-ups...")
response = requests.get(
    f"{BASE_URL}/dashboard/upcoming-followups",
    headers=headers,
    params={"days": 7}
)
upcoming = response.json()
print(f"\nYou have {upcoming['count']} follow-ups scheduled in the next 7 days:")
for followup in upcoming['followups']:
    print(f"  - {followup['name']} ({followup['university']}): {followup['follow_up_date'][:10]}")
```

### Example 4: Document Management

```python
import requests

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token-here"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Upload CV
print("Uploading CV...")
with open("my_cv.pdf", "rb") as f:
    files = {"file": ("cv.pdf", f, "application/pdf")}
    data = {"description": "My academic CV - Updated October 2025"}
    
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )
    cv_doc_id = response.json()["id"]
    print(f"✓ CV uploaded (ID: {cv_doc_id})")

# Upload SOP for specific contact
print("\nUploading personalized SOP...")
contact_id = 1  # Replace with actual contact ID
with open("sop_stanford.pdf", "rb") as f:
    files = {"file": ("sop.pdf", f, "application/pdf")}
    data = {
        "contact_id": contact_id,
        "description": "Statement of Purpose for Stanford application"
    }
    
    response = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )
    sop_doc_id = response.json()["id"]
    print(f"✓ SOP uploaded (ID: {sop_doc_id})")

# List all documents
print("\nListing all documents...")
response = requests.get(
    f"{BASE_URL}/documents/",
    headers=headers
)
documents = response.json()
print(f"You have {len(documents)} documents:")
for doc in documents:
    contact_info = f" (linked to contact {doc['contact_id']})" if doc['contact_id'] else ""
    print(f"  - {doc['original_filename']}{contact_info}")

# Download a document
print(f"\nDownloading document {cv_doc_id}...")
response = requests.get(
    f"{BASE_URL}/documents/{cv_doc_id}/download",
    headers=headers
)
with open("downloaded_cv.pdf", "wb") as f:
    f.write(response.content)
print("✓ Document downloaded")
```

### Example 5: Dashboard Analytics & Activity Tracking

```python
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token-here"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Get comprehensive dashboard stats
print("=== Dashboard Overview ===\n")

# Overall statistics
response = requests.get(f"{BASE_URL}/dashboard/stats", headers=headers)
stats = response.json()

print("📊 Contact Statistics:")
print(f"  Total Contacts: {stats['contacts']['total']}")
print(f"  Contacted: {stats['contacts']['contacted']}")
print(f"  Received Replies: {stats['contacts']['replied']}")
print(f"  Pending Action: {stats['contacts']['pending']}")
print(f"  Follow-ups Scheduled: {stats['contacts']['follow_ups_scheduled']}")
print(f"  Response Rate: {stats['contacts']['response_rate']}%")

print(f"\n📧 Recent Activity:")
print(f"  Emails sent (last 7 days): {stats['activity']['emails_sent_last_7_days']}")

print(f"\n📁 Resources:")
print(f"  Templates: {stats['resources']['templates']}")
print(f"  Documents: {stats['resources']['documents']}")

# Pipeline overview
print("\n=== Outreach Pipeline ===\n")
response = requests.get(f"{BASE_URL}/dashboard/pipeline", headers=headers)
pipeline = response.json()["pipeline"]

for stage in pipeline:
    print(f"{stage['status'].upper()}: {stage['count']} contacts")
    if stage['contacts']:
        print("  Recent:")
        for contact in stage['contacts'][:3]:
            print(f"    - {contact['name']} ({contact['university']})")
    print()

# Recent activity log
print("=== Recent Activity Log ===\n")
response = requests.get(
    f"{BASE_URL}/dashboard/activity",
    headers=headers,
    params={"page": 1, "page_size": 10}
)
activities = response.json()

print(f"Last {len(activities['logs'])} activities:")
for activity in activities['logs']:
    timestamp = datetime.fromisoformat(activity['created_at'].replace('Z', '+00:00'))
    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
    print(f"  [{time_str}] {activity['title']}")
    if activity['description']:
        print(f"    └─ {activity['description']}")

# Contact statistics by status
print("\n=== Contact Status Breakdown ===\n")
response = requests.get(
    f"{BASE_URL}/contacts/stats/summary",
    headers=headers
)
stats = response.json()

for status, count in stats.items():
    if status != "total":
        percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
```

### Example 6: Advanced Template Personalization

```python
import requests

BASE_URL = "http://localhost:8000/api"
TOKEN = "your-jwt-token-here"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Create a sophisticated template with multiple placeholders
template_response = requests.post(
    f"{BASE_URL}/templates/",
    headers=headers,
    json={
        "name": "Research Collaboration Proposal",
        "subject": "Collaboration Opportunity: [ResearchTopic] at [University]",
        "body": """Dear Professor [ProfName],

I hope this message finds you well. My name is Jane Doe, and I am currently completing my Master's degree in Computer Science at XYZ University.

I have been following your work on [ResearchInterest] with great interest, particularly your recent publications. The intersection of my research experience in neural networks and your work on [ResearchTopic] presents an exciting opportunity for potential collaboration or graduate study.

My thesis focuses on efficient deep learning architectures, and I believe the methodologies I've developed could complement your ongoing research at [University]'s [Department].

I would be honored to discuss:
1. Potential PhD positions in your research group
2. Collaborative research opportunities
3. Your insights on current trends in [ResearchInterest]

I have attached my CV, research statement, and a summary of my recent work. I am happy to schedule a call at your convenience to discuss how my background might contribute to your team's objectives.

Thank you for considering my inquiry. I look forward to the possibility of working together.

Best regards,
Jane Doe
Master's Student, Computer Science
XYZ University
jane.doe@university.edu""",
        "use_ai_personalization": True,
        "description": "Professional collaboration proposal template"
    }
)
template_id = template_response.json()["id"]

# Test personalization with AI
contact_id = 1  # Replace with actual contact ID

# Without AI (basic placeholder replacement)
print("=== Basic Personalization ===\n")
response = requests.post(
    f"{BASE_URL}/templates/personalize",
    headers=headers,
    params={"use_ai": False},
    json={
        "template_id": template_id,
        "contact_id": contact_id
    }
)
basic = response.json()
print("Subject:", basic['subject'])
print("\nBody:", basic['body'][:200], "...")

# With AI enhancement
print("\n\n=== AI-Enhanced Personalization ===\n")
response = requests.post(
    f"{BASE_URL}/templates/personalize",
    headers=headers,
    params={"use_ai": True},
    json={
        "template_id": template_id,
        "contact_id": contact_id,
        "additional_context": """
        - Reference their ICLR 2024 paper on neural architecture search
        - Mention my experience with PyTorch and TensorFlow
        - Express interest in their current NSF grant on efficient AI
        """
    }
)
ai_enhanced = response.json()
print("Subject:", ai_enhanced['subject'])
print("\nBody:", ai_enhanced['body'])

# Compare
print("\n\n=== Comparison ===")
print(f"Original subject length: {len(basic['original_subject'])} chars")
print(f"AI subject length: {len(ai_enhanced['subject'])} chars")
print(f"\nOriginal body length: {len(basic['original_body'])} chars")
print(f"AI body length: {len(ai_enhanced['body'])} chars")
```

## Testing the API

### Quick Health Check

```bash
# Check if API is running
curl http://localhost:8000/api/health
```

### Authentication Flow

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"

# Response:
# {"access_token":"eyJ0eXAiOiJKV1QiLCJhbGc...","token_type":"bearer"}

# Save token
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

# Get current user info
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Common Workflows

### Daily Usage Pattern

1. **Morning**: Check dashboard for pending actions
2. **Add contacts**: Import from LinkedIn/conferences
3. **Personalize emails**: Use AI for key contacts
4. **Send batch**: Send to 5-10 contacts per day
5. **Track responses**: Update contact status
6. **Schedule follow-ups**: For non-responders after 2 weeks

### Weekly Review

1. Check pipeline status
2. Review activity logs
3. Update contact notes
4. Schedule next batch
5. Analyze response rates

### Best Practices

1. **Rate Limiting**: Don't send more than 20-30 emails per day
2. **Personalization**: Always use AI for important contacts
3. **Follow-ups**: Wait 2 weeks before follow-up
4. **Documentation**: Keep detailed notes on each contact
5. **Templates**: Maintain 2-3 templates for different scenarios

## Error Handling

```python
import requests

def safe_api_call(method, url, **kwargs):
    """Wrapper for API calls with error handling."""
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to API")
        return None
    except requests.exceptions.Timeout:
        print("Timeout Error: Request took too long")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
result = safe_api_call(
    "POST",
    f"{BASE_URL}/contacts/",
    headers=headers,
    json=contact_data
)
if result:
    print(f"Success: {result}")
```

---

For more examples, see the API documentation at http://localhost:8000/api/docs
