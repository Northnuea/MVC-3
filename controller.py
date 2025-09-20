from flask import Flask, render_template, request, redirect, url_for, session
import model as db
import uuid
from datetime import datetime
import webbrowser
import time

app = Flask(__name__, template_folder='view')
# ตั้งค่าคีย์ลับสำหรับจัดการ Session ซึ่งจำเป็นสำหรับการล็อกอิน
app.secret_key = 'super_secret_key' 

# เส้นทางสำหรับหน้าล็อกอิน
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # รับข้อมูลชื่อผู้ใช้จากฟอร์ม
        username = request.form['username']
        # ตรวจสอบชื่อผู้ใช้กับฐานข้อมูล
        user_id = db.authenticate(username)
        if user_id:
            # ถ้าผู้ใช้ถูกต้อง ให้เก็บ user_id ไว้ใน session
            session['user_id'] = user_id
            # redirect ไปยังหน้ารวมโครงการ
            return redirect(url_for('project_list'))
    # แสดงหน้าล็อกอิน
    return render_template('login.html')

# เส้นทางสำหรับออกจากระบบ
@app.route('/logout')
def logout():
    # ลบ user_id ออกจาก session
    session.pop('user_id', None)
    # redirect กลับไปยังหน้ารวมโครงการ
    return redirect(url_for('project_list'))

# เส้นทางสำหรับหน้ารวมโครงการ
@app.route('/')
def project_list():
    # ดึงข้อมูลโครงการและหมวดหมู่ทั้งหมดจาก Model
    projects = db.get_projects()
    categories = db.get_categories()
    
    # รับค่าการค้นหาและฟิลเตอร์จาก URL
    query = request.args.get('q')
    category_filter = request.args.get('category')
    sort_by = request.args.get('sort_by', 'newest')
    
    # ถ้ามีการค้นหา ให้กรองโครงการตามคำค้นหา
    if query:
        projects = db.search_projects(projects, query)
    
    # ถ้ามีการฟิลเตอร์หมวดหมู่ ให้กรองโครงการตามหมวดหมู่ที่เลือก
    if category_filter:
        projects = db.filter_projects_by_category(projects, category_filter)

    # จัดเรียงโครงการตามตัวเลือกที่กำหนด
    projects = db.sort_projects(projects, sort_by)
    
    # คำนวณความคืบหน้าของแต่ละโครงการและตรวจสอบวันหมดอายุ
    for p in projects:
        p['progress'] = (p['current_amount'] / p['target_amount']) * 100 if p['target_amount'] > 0 else 0
        p['is_expired'] = datetime.strptime(p['deadline'], '%Y-%m-%d').date() < datetime.now().date()
        
    # แสดงผลหน้า index.html พร้อมส่งข้อมูลที่ประมวลผลแล้ว
    return render_template('index.html', projects=projects, categories=categories, 
                           selected_category=category_filter, sort_by=sort_by)

# เส้นทางสำหรับหน้ารายละเอียดโครงการ
@app.route('/project/<project_id>')
def project_details(project_id):
    # ดึงข้อมูลโครงการและรางวัลตาม project_id
    project = db.get_project(project_id)
    if not project:
        return "Project not found", 404
        
    rewards = db.get_rewards_for_project(project_id)
    
    # คำนวณความคืบหน้าและตรวจสอบวันหมดอายุของโครงการ
    project['progress'] = (project['current_amount'] / project['target_amount']) * 100 if project['target_amount'] > 0 else 0
    project['is_expired'] = datetime.strptime(project['deadline'], '%Y-%m-%d').date() < datetime.now().date()
    
    # แสดงผลหน้า project.html พร้อมส่งข้อมูล
    return render_template('project.html', project=project, rewards=rewards, user_id=session.get('user_id'))

# เส้นทางสำหรับจัดการการสนับสนุนโครงการ
@app.route('/pledge/<project_id>', methods=['POST'])
def pledge(project_id):
    # ตรวจสอบว่าผู้ใช้ล็อกอินอยู่หรือไม่
    user_id = session.get('user_id')
    if not user_id:
        return "Please login to pledge.", 401
    
    # รับจำนวนเงินและรหัสรางวัลจากฟอร์ม
    amount = float(request.form['amount'])
    reward_id = request.form.get('reward_id')

    # เรียกใช้ฟังก์ชันใน Model เพื่อทำการสนับสนุน
    is_success, message = db.create_pledge(user_id, project_id, amount, reward_id)
    
    if not is_success:
        return f"Pledge failed: {message}", 400
        
    # ถ้าสำเร็จให้ redirect กลับไปยังหน้ารายละเอียดโครงการ
    return redirect(url_for('project_details', project_id=project_id))

# เส้นทางสำหรับหน้าสถิติ
@app.route('/stats')
def stats():
    # ดึงข้อมูลการสนับสนุนทั้งหมดจาก Model
    pledges = db.get_all_pledges()
    # นับจำนวนการสนับสนุนที่สำเร็จและถูกปฏิเสธ
    success_count = sum(1 for p in pledges if p['status'] == 'success')
    rejected_count = sum(1 for p in pledges if p['status'] == 'rejected')
    
    # แสดงผลหน้า stats.html พร้อมส่งข้อมูลสถิติ
    return render_template('stats.html', success_count=success_count, rejected_count=rejected_count)

# บล็อกสำหรับรันโปรแกรม
if __name__ == '__main__':
    # โหลดข้อมูลเริ่มต้นจาก db.json
    db.load_data()
    # หน่วงเวลา 1 วินาทีเพื่อให้เซิร์ฟเวอร์พร้อม
    time.sleep(1) 
    # เปิดเบราว์เซอร์ไปยังหน้าแรกโดยอัตโนมัติ
    webbrowser.open_new('http://127.0.0.1:5000/')
    # เริ่มเซิร์ฟเวอร์ Flask
    app.run(debug=True)