import json
import os
import uuid
from datetime import datetime

# กำหนดชื่อไฟล์ฐานข้อมูล
DB_FILE = 'db.json'
db_data = {}

# โหลดข้อมูลจากไฟล์ JSON
def load_data():
    global db_data
    # ถ้าไม่มีไฟล์ db.json ให้สร้างข้อมูลตัวอย่างขึ้นมา
    if not os.path.exists(DB_FILE):
        print("db.json not found. Creating sample data...")
        create_sample_data()
    
    # เปิดไฟล์และโหลดข้อมูล
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        db_data = json.load(f)
        
# บันทึกข้อมูลลงในไฟล์ JSON
def save_data():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)

# ฟังก์ชันสำหรับดึงข้อมูลต่างๆ
def get_projects():
    return db_data.get('projects', [])

def get_project(project_id):
    for p in db_data.get('projects', []):
        if p['project_id'] == project_id:
            return p
    return None

def get_categories():
    return db_data.get('categories', [])

def get_rewards_for_project(project_id):
    return [r for r in db_data.get('reward_tiers', []) if r['project_id'] == project_id]

def get_reward(reward_id):
    for r in db_data.get('reward_tiers', []):
        if r['reward_id'] == reward_id:
            return r
    return None

def get_all_pledges():
    return db_data.get('pledges', [])

def authenticate(username):
    for user in db_data.get('users', []):
        if user['username'] == username:
            return user['user_id']
    return None

# ฟังก์ชันหลักสำหรับการสร้างการสนับสนุน
def create_pledge(user_id, project_id, amount, reward_id):
    project = get_project(project_id)
    if not project:
        return False, "Project not found."

    # ตรวจสอบกฎทางธุรกิจ: วันหมดอายุโครงการ
    if datetime.strptime(project['deadline'], '%Y-%m-%d').date() < datetime.now().date():
        save_pledge_status(user_id, project_id, amount, reward_id, 'rejected')
        return False, "Project has already expired."
        
    reward = None
    if reward_id:
        reward = get_reward(reward_id)
        if not reward:
            save_pledge_status(user_id, project_id, amount, reward_id, 'rejected')
            return False, "Reward not found."
        
        # ตรวจสอบกฎทางธุรกิจ: ยอดเงินขั้นต่ำ
        if amount < reward['min_pledge']:
            save_pledge_status(user_id, project_id, amount, reward_id, 'rejected')
            return False, "Pledge amount is less than the minimum for the selected reward."
            
        # ตรวจสอบกฎทางธุรกิจ: โควตารางวัล
        if reward['quota'] is not None and reward['quota'] <= 0:
            save_pledge_status(user_id, project_id, amount, reward_id, 'rejected')
            return False, "Selected reward is out of stock."

    # อัปเดตข้อมูล: เพิ่มยอดรวมโครงการ
    project['current_amount'] += amount
    if reward:
        # อัปเดตข้อมูล: ลดโควตารางวัล
        if reward['quota'] is not None:
            reward['quota'] -= 1
    
    # บันทึกสถานะการสนับสนุนและข้อมูลที่อัปเดต
    save_pledge_status(user_id, project_id, amount, reward_id, 'success')
    save_data()
    return True, "Pledge successful."

# ฟังก์ชันสำหรับบันทึกสถานะการสนับสนุน
def save_pledge_status(user_id, project_id, amount, reward_id, status):
    new_pledge = {
        "pledge_id": str(uuid.uuid4()),
        "user_id": user_id,
        "project_id": project_id,
        "timestamp": datetime.now().isoformat(),
        "amount": amount,
        "reward_id": reward_id,
        "status": status
    }
    db_data['pledges'].append(new_pledge)
    save_data()

# ฟังก์ชันสำหรับการค้นหา ฟิลเตอร์ และเรียงลำดับ
def search_projects(projects, query):
    return [p for p in projects if query.lower() in p['title'].lower()]

def filter_projects_by_category(projects, category_id):
    return [p for p in projects if p['category_id'] == category_id]

def sort_projects(projects, sort_by):
    if sort_by == 'newest':
        return sorted(projects, key=lambda p: p.get('created_at', ''), reverse=True)
    elif sort_by == 'deadline':
        return sorted(projects, key=lambda p: datetime.strptime(p['deadline'], '%Y-%m-%d'))
    elif sort_by == 'most_funded':
        return sorted(projects, key=lambda p: p['current_amount'], reverse=True)
    return projects

# ฟังก์ชันสำหรับสร้างข้อมูลจำลอง
def create_sample_data():
    sample_data = {
        "users": [
            {"user_id": "user-1", "username": "alice", "password": "pass"},
            {"user_id": "user-2", "username": "bob", "password": "pass"},
            {"user_id": "user-3", "username": "charlie", "password": "pass"},
            {"user_id": "user-4", "username": "david", "password": "pass"},
            {"user_id": "user-5", "username": "eve", "password": "pass"},
            {"user_id": "user-6", "username": "frank", "password": "pass"},
            {"user_id": "user-7", "username": "grace", "password": "pass"},
            {"user_id": "user-8", "username": "heidi", "password": "pass"},
            {"user_id": "user-9", "username": "ivan", "password": "pass"},
            {"user_id": "user-10", "username": "judy", "password": "pass"},
        ],
        "categories": [
            {"category_id": "cat-1", "name": "Technology"},
            {"category_id": "cat-2", "name": "Arts"},
            {"category_id": "cat-3", "name": "Community"},
        ],
        "projects": [
            {
                "project_id": "12345678", "title": "AI-Powered Learning App", 
                "target_amount": 50000.0, "deadline": "2025-12-31", 
                "current_amount": 25000.0, "category_id": "cat-1", "created_at": "2025-09-01T10:00:00"
            },
            {
                "project_id": "23456789", "title": "Local Art Exhibition", 
                "target_amount": 10000.0, "deadline": "2025-11-15", 
                "current_amount": 8000.0, "category_id": "cat-2", "created_at": "2025-09-02T11:00:00"
            },
            {
                "project_id": "34567890", "title": "Community Garden", 
                "target_amount": 5000.0, "deadline": "2025-10-30", 
                "current_amount": 3000.0, "category_id": "cat-3", "created_at": "2025-09-03T12:00:00"
            },
            {
                "project_id": "45678901", "title": "Robotics Club Kits", 
                "target_amount": 15000.0, "deadline": "2026-01-20", 
                "current_amount": 0.0, "category_id": "cat-1", "created_at": "2025-09-04T13:00:00"
            },
            {
                "project_id": "56789012", "title": "Digital Photography Workshop", 
                "target_amount": 7500.0, "deadline": "2025-12-01", 
                "current_amount": 7500.0, "category_id": "cat-2", "created_at": "2025-09-05T14:00:00"
            },
            {
                "project_id": "67890123", "title": "Clean Water Initiative", 
                "target_amount": 20000.0, "deadline": "2025-12-25", 
                "current_amount": 18000.0, "category_id": "cat-3", "created_at": "2025-09-06T15:00:00"
            },
            {
                "project_id": "78901234", "title": "VR Educational Games", 
                "target_amount": 30000.0, "deadline": "2026-02-14", 
                "current_amount": 10000.0, "category_id": "cat-1", "created_at": "2025-09-07T16:00:00"
            },
            {
                "project_id": "89012345", "title": "Outdoor Mural Project", 
                "target_amount": 9000.0, "deadline": "2025-11-20", 
                "current_amount": 4500.0, "category_id": "cat-2", "created_at": "2025-09-08T17:00:00"
            },
            {
                "project_id": "90123456", "title": "Youth Leadership Program", 
                "target_amount": 12000.0, "deadline": "2025-12-10", 
                "current_amount": 1000.0, "category_id": "cat-3", "created_at": "2025-09-09T18:00:00"
            },
        ],
        "reward_tiers": [
            {"reward_id": "r-1", "project_id": "12345678", "title": "Digital Thank You Note", "min_pledge": 10.0, "quota": None},
            {"reward_id": "r-2", "project_id": "12345678", "title": "Early Access & Beta Tester", "min_pledge": 50.0, "quota": 100},
            {"reward_id": "r-3", "project_id": "23456789", "title": "Mention in Exhibition Booklet", "min_pledge": 25.0, "quota": None},
            {"reward_id": "r-4", "project_id": "23456789", "title": "Signed Poster", "min_pledge": 100.0, "quota": 20},
            {"reward_id": "r-5", "project_id": "34567890", "title": "Seed Pack", "min_pledge": 15.0, "quota": 50},
            {"reward_id": "r-6", "project_id": "34567890", "title": "Name a Plant", "min_pledge": 50.0, "quota": 10},
            {"reward_id": "r-7", "project_id": "45678901", "title": "Thank You Email", "min_pledge": 5.0, "quota": None},
            {"reward_id": "r-8", "project_id": "45678901", "title": "Full Robotics Kit", "min_pledge": 200.0, "quota": 15},
            {"reward_id": "r-9", "project_id": "56789012", "title": "Free E-Book", "min_pledge": 20.0, "quota": None},
            {"reward_id": "r-10", "project_id": "56789012", "title": "One-on-One Session", "min_pledge": 150.0, "quota": 5},
            {"reward_id": "r-11", "project_id": "67890123", "title": "Digital Certificate", "min_pledge": 10.0, "quota": None},
            {"reward_id": "r-12", "project_id": "67890123", "title": "Project T-shirt", "min_pledge": 75.0, "quota": 30},
            {"reward_id": "r-13", "project_id": "78901234", "title": "VR Demo Access", "min_pledge": 30.0, "quota": None},
            {"reward_id": "r-14", "project_id": "78901234", "title": "Your Name in Credits", "min_pledge": 100.0, "quota": 25},
            {"reward_id": "r-15", "project_id": "89012345", "title": "Digital Wallpaper", "min_pledge": 5.0, "quota": None},
            {"reward_id": "r-16", "project_id": "89012345", "title": "Guided Mural Tour", "min_pledge": 50.0, "quota": 15},
            {"reward_id": "r-17", "project_id": "90123456", "title": "Sticker Pack", "min_pledge": 15.0, "quota": 100},
            {"reward_id": "r-18", "project_id": "90123456", "title": "Leadership Guide Book", "min_pledge": 60.0, "quota": 50},
        ],
        "pledges": [
            {"pledge_id": str(uuid.uuid4()), "user_id": "user-1", "project_id": "12345678", "timestamp": "2025-09-10T09:00:00", "amount": 50.0, "reward_id": "r-2", "status": "success"},
            {"pledge_id": str(uuid.uuid4()), "user_id": "user-2", "project_id": "12345678", "timestamp": "2025-09-10T10:00:00", "amount": 100.0, "reward_id": "r-2", "status": "success"},
            {"pledge_id": str(uuid.uuid4()), "user_id": "user-3", "project_id": "23456789", "timestamp": "2025-09-10T11:00:00", "amount": 10.0, "reward_id": "r-4", "status": "rejected"},
            {"pledge_id": str(uuid.uuid4()), "user_id": "user-4", "project_id": "23456789", "timestamp": "2025-09-11T12:00:00", "amount": 25.0, "reward_id": "r-3", "status": "success"},
            {"pledge_id": str(uuid.uuid4()), "user_id": "user-5", "project_id": "34567890", "timestamp": "2025-09-11T13:00:00", "amount": 50.0, "reward_id": "r-6", "status": "success"},
        ]
    }
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=4, ensure_ascii=False)
    
    global db_data
    db_data = sample_data