import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
# ---------- 🔹 Load .env ----------
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# ---------- 🔹 Scrape Gold Prices ----------
def extract_table_prices(soup, carat_label):
    sections = soup.find_all("section")
    gold_data = {}

    for section in sections:
        headline = section.find("h2", class_="table-headLine")
        if headline and carat_label.lower() in headline.text.lower():
            table = section.find("table", class_="table-conatiner")
            rows = table.find("tbody").find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    gram = cols[0].text.strip()
                    today = cols[1].text.strip()
                    yesterday = cols[2].text.strip()
                    change = cols[3].text.strip()
                    gold_data[gram] = {
                        "Today": today,
                        "Yesterday": yesterday,
                        "Change": change
                    }
            break

    return gold_data

def get_gold_price_table_html():
    url = "https://www.goodreturns.in/gold-rates/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        gold_24k = extract_table_prices(soup, "24 Carat")
        gold_22k = extract_table_prices(soup, "22 Carat")

        html = f"<h2> Gold Prices in India - {datetime.now():%Y-%m-%d %H:%M}</h2>"

        def build_table(title, data):
            rows = ""
            for gram in ["1", "8", "10"]:
                if gram in data:
                    d = data[gram]
                    rows += f"<tr><td>{gram}g</td><td>{d['Today']}</td><td>{d['Yesterday']}</td><td>{d['Change']}</td></tr>"
            return f"""
                <h3>{title}</h3>
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
                    <tr style="background-color:#f2f2f2;"><th>Gram</th><th>Today</th><th>Yesterday</th><th>Change</th></tr>
                    {rows}
                </table>
                <br>
            """

        html += build_table("24K Gold", gold_24k)
        html += build_table("22K Gold", gold_22k)

        return html

    except Exception as e:
        return f"<p>Error fetching gold data: {e}</p>"


def send_email(subject, html_body):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# ---------- 🔹 Run ----------
if __name__ == "__main__":
    report_html = get_gold_price_table_html()
    print(report_html)  # Optional console output
    send_email("Daily Gold Price Report (1g, 8g, 10g)", report_html)
