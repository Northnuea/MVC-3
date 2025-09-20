import webbrowser
import time
import controller
import model as db

if __name__ == '__main__':
    # โหลดข้อมูลเริ่มต้นจาก db.json
    db.load_data()
    
    # หน่วงเวลา 1 วินาทีเพื่อให้เซิร์ฟเวอร์พร้อม
    time.sleep(1)
    
    # เปิดเบราว์เซอร์ไปยังหน้าแรกโดยอัตโนมัติ
    webbrowser.open_new('http://127.0.0.1:5000/')
    controller.app.run(debug=True)