# app.py (오늘 날짜 데이터 추출 수정본)

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from flask_cors import CORS
import urllib3
from datetime import datetime

# SSL 인증서 경고 메시지를 숨기기 위한 설정
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 사용자 설정 ---
LOGIN_INFO = {
    "gcnong": {"id": "rootx", "pw": "aa1707aa"},    
    "wandoman": {"id": "rootx", "pw": "aa1707aa"},  
    "susanchon": {"id": "rootx", "pw": "aa1707aa"},  
    "hadonggol": {"id": "rootx", "pw": "aa1707aa"},  
    "hnhwangtogol": {"id": "rootx", "pw": "aa1707aa"},  
    "hcnong": {"id": "rootx", "pw": "aa1707aa"},  
    "suhofarm": {"id": "rootx", "pw": "aa1707aa"},  
    "youngheefarm": {"id": "rootx", "pw": "aa1707aa"},  
    "seongjunong": {"id": "rootx", "pw": "aa1707aa"},  
    # ... 이런 식으로 10개까지 계속 추가하시면 됩니다.
    # "사이트주소의고유한부분": {"id": "아이디", "pw": "비밀번호"},
}
def clean_data(text):
    """데이터를 정제하는 함수"""
    try:
        if not text or not text.strip(): return 0
        cleaned_text = text.replace(',', '').replace('%', '').strip()
        return int(cleaned_text) if '.' not in cleaned_text else float(cleaned_text)
    except (ValueError, AttributeError):
        return 0

def scrape_site_data(site_name, credentials):
    """하나의 사이트에 접속하여 '오늘 날짜'의 매출 데이터를 가져오는 함수"""
    print(f"-> '{site_name}' 사이트 처리 시작...")
    
    base_url = f"https://{site_name}.com/root"
    login_url = f"{base_url}/login.php"
    target_url = f"{base_url}/shop.state.main.php"
    login_payload = { 'a': 'login', 'id': credentials['id'], 'pw': credentials['pw'] }

    try:
        with requests.Session() as s:
            login_res = s.post(login_url, data=login_payload, verify=False, timeout=30)
            login_res.encoding = 'euc-kr'
            if "아이디 또는 비밀번호" in login_res.text:
                print(f"[실패] '{site_name}' 로그인 실패.")
                return None

            target_res = s.get(target_url, verify=False, timeout=30)
            target_res.encoding = 'euc-kr'
            
            soup = BeautifulSoup(target_res.text, 'lxml')
            title_tag = soup.find('b', string='일별 매출분석')
            if not title_tag:
                print(f"[실패] '{site_name}'에서 '일별 매출분석' 테이블을 찾지 못했습니다.")
                return None

            # ▼▼▼ 로직 수정: 오늘 날짜의 행을 찾아 데이터 추출 ▼▼▼
            today_str = f"{datetime.now().day:02d}일" # 예: "16일"
            daily_sales_table = title_tag.find_parent('table').find_next_sibling('table')
            rows = daily_sales_table.find_all('tr')
            
            todays_data_row = None
            for row in rows[1:-1]: # 헤더와 합계 행 제외
                cols = row.find_all('td')
                if len(cols) > 0 and cols[0].text.strip().startswith(today_str):
                    todays_data_row = cols
                    break
            
            if not todays_data_row:
                print(f"[정보] '{site_name}'에서 오늘({today_str})자 데이터를 찾을 수 없습니다.")
                return {'주문건수': 0, '매출액': 0, '매입액': 0, '순익': 0, '마진': 0}

            result = {
                '주문건수': clean_data(todays_data_row[1].text),
                '매출액': clean_data(todays_data_row[7].text),
                '매입액': clean_data(todays_data_row[8].text),
                '순익': clean_data(todays_data_row[9].text),
                '마진': clean_data(todays_data_row[10].text)
            }
            print(f"[성공] '{site_name}' 오늘 데이터 수집 완료.")
            return result
            # ▲▲▲ 로직 수정 완료 ▲▲▲

    except Exception as e:
        print(f"[오류] '{site_name}' 처리 중 오류 발생: {e}")
        return None


# --- Flask 웹 서버 설정 ---
app = Flask(__name__)
CORS(app)

@app.route('/get-sales-data')
def get_sales_data():
    all_sites_data = {}
    for site, creds in LOGIN_INFO.items():
        all_sites_data[site] = scrape_site_data(site, creds)
    
    return jsonify(all_sites_data)

if __name__ == '__main__':
    print("통합 대시보드 백엔드 서버를 시작합니다.")
    app.run(port=5000)