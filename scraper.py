from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, request, render_template
from datetime import datetime, timedelta
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3
import numpy

con = sqlite3.connect("forex.db")
cur = con.cursor()
createtable = """
    CREATE TABLE IF NOT EXISTS rates (
        beforecurrency TEXT,
        aftercurrency TEXT,
        datadate DATE, 
        open TEXT, 
        high TEXT, 
        low TEXT, 
        close TEXT, 
        adj_close TEXT, 
        volume TEXT
    )
"""

inserttable = """
            INSERT INTO rates (
                beforecurrency, 
                aftercurrency, 
                datadate, 
                open, 
                high, 
                low, 
                close, 
                adj_close, 
                volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

queryrates = """
    SELECT open FROM rates 
            WHERE beforecurrency = '{from_cur}' AND aftercurrency = '{to_cur}' 
            AND datadate BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY datadate
"""

cur.execute(createtable)
con.commit()


def scrape_yahoo_finance(quote):
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Increase timeout and add page load strategy
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(100)  # Increase page load timeout

    end_date = int(datetime.datetime.now().timestamp())
    start_date = int(get_time('1M').timestamp())
    
    try:
        # Construct URL with parameters
        url = f"https://finance.yahoo.com/quote/{quote}/history/?period1={start_date}&period2={end_date}"
        driver.get(url)
        
        # Wait for specific element to ensure page is loaded
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        
        # Rest of your scraping logic
        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        
        for row in table_rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            column_texts = [column.text for column in columns]
            # Convert to a datetime object
            date_obj = datetime.datetime.strptime(column_texts[0], "%b %d, %Y")

            # Format as "YYYY-MM-DD"
            formatted_date = date_obj.strftime("%Y-%m-%d")

            cur.execute(inserttable, 
                        (quote[0:3], quote[3:6],formatted_date,column_texts[1],column_texts[2],column_texts[3],column_texts[4],column_texts[5],column_texts[6]))
            con.commit()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()

def get_time(period):
    end_date = datetime.datetime.now()

    period_map = {
        '1W': timedelta(days=7),
        '1M': timedelta(days=30),
        '3M': timedelta(days=90),
        '6M': timedelta(days=180),
        '1Y': timedelta(days=365)
    }

    start_date = end_date - period_map[period]
    return start_date

def plotting(from_cur, to_cur, period):
    con = sqlite3.connect("forex.db")
    cur = con.cursor()
    end_date = datetime.datetime.now().date()
    start_date = get_time(period).date()
    query = queryrates.format(from_cur=from_cur, to_cur=to_cur, start_date=start_date, end_date=end_date)
    cur.execute(query)
    y = cur.fetchall()
    array = numpy.array([float(item[0]) for item in y])
    L = []
    for i in range (len(y)):
        L.append([start_date+timedelta(days=i)])

    plt.figure(figsize=(10, 6))
    plt.plot(L, array, marker='o', linestyle='-', color='b', label='Exchange Rate')
    plt.xlabel('Date')
    plt.ylabel('Exchange Rate')
    plt.title(f'{from_cur} to {to_cur} Exchange Rate Over Time ({period})')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.savefig("linechart.jpg")



#scrape_yahoo_finance("EURUSD%3DX")
cur.close()
con.close()

app = Flask(__name__)
@app.route("/")
def hello():
    return "Hello World"

@app.route('/api/forex-data', methods=['POST'])
def get_forex_data():
    con = sqlite3.connect("forex.db")
    cur = con.cursor()
    data = request.get_json()
    from_currency = data.get('from')
    to_currency = data.get('to')
    period = data.get('period', '1M')
    end_date = datetime.datetime.now().date()
    start_date = get_time(period).date()
    query = queryrates.format(from_cur=from_currency, to_cur=to_currency, start_date=start_date, end_date=end_date)
    cur.execute(query)
    return jsonify(cur.fetchall())

@app.route('/api/trigger', methods=['POST'])
def run_periodic_scraper():
    scheduler = BlockingScheduler()
    data = request.get_json()
    from_currency = data.get('from')
    to_currency = data.get('to')
    quote = from_currency+to_currency+"%3DX"
    scheduler.add_job(scrape_yahoo_finance(quote), 'interval', days=1)
    scheduler.start()

@app.route('/app/plot', methods = ['POST'])
def trigger():
    data = request.get_json()
    from_currency = data.get('from')
    to_currency = data.get('to')
    period = data.get('period', '1M')
    plotting(from_currency, to_currency, period)
    return "Image Created !"