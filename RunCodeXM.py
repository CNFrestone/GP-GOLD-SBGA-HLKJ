from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

@app.route('/get_stock_info', methods=['GET'])
def get_stock_info():
    options = Options()
    options.add_argument('--headless')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get('https://m.cngold.org/quote/gjs/yhzhj_ghzhj1.html')
    time.sleep(3)

    stock_info_section = driver.find_element(By.CSS_SELECTOR, 'section#stock_info_container.stock_info_2.nav_bg_red')
    html_content = stock_info_section.get_attribute('outerHTML')
    driver.quit()

    soup = BeautifulSoup(html_content, 'html.parser')

    name = soup.find(id='quoteTitle').text
    stock = soup.find(id='quoteCode').text.strip('()')
    price = f"{float(soup.find(id='quotePrice').text):.2f}"
    rate = soup.find(id='quotePercent').text.strip('%')
    quote_updown = soup.find(id='quoteUpdown').text

    if quote_updown.startswith('+'):
        rate = '+' + rate
    elif quote_updown.startswith('-'):
        rate = '-' + rate

    time_show = soup.find(id='timeShow').text
    valid = 0 if "已收盘" in time_show else 1

    combined_output = {
        "Selenium": {
            "name": name,
            "stock": stock,
            "price": price,
            "rate": rate + '%',
            "valid": valid
        },
        "yfinance": []
    }

    stocks = {
        '301011.SZ': '华立科技',
        '6460.T': '世嘉飒美'
    }

    current_time = datetime.now()

    for stock_code, stock_name in stocks.items():
        stock = yf.Ticker(stock_code)
        historical_data = stock.history(period='5d')
        valid = 0

        if historical_data.empty or len(historical_data) < 2:
            continue
        else:
            latest_price = f"{historical_data['Close'].iloc[-1]:.2f}"
            previous_price = historical_data['Close'].iloc[-2]
            price_change = float(latest_price) - previous_price
            percentage_change = (price_change / previous_price) * 100

            if current_time.weekday() < 5 and (9 <= current_time.hour < 15):
                valid = 1

            rate = round(float(percentage_change), 2)
            if rate > 0:
                rate = f"+{rate}"

            stock_info = {
                'name': stock_name,
                'stock': stock_code,
                'price': latest_price,
                'rate': f"{rate}%",
                'valid': valid
            }

            combined_output["yfinance"].append(stock_info)

    return jsonify(combined_output)

if __name__ == '__main__':
    app.run(debug=True)
