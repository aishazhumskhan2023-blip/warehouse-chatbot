# 📦 WarehouseBot — Warehouse Catalog Chatbot

## 1. Project Name

WarehouseBot — a chatbot for warehouse inventory management

---

## 2. Project Description

WarehouseBot is a web application in the form of a chatbot for warehouse management.
The user opens the website in a browser and communicates with the bot using text commands.

The bot can:
- add products to the warehouse
- process incoming and outgoing stock
- show the balance of each product
- search for products by name or supplier
- generate reports and statistics
- show the history of all operations
- warn when a product is running low
- save the entire message history to a database

---

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python 3 | Main programming language |
| Flask | Web framework, request handling |
| SQLite | Database, storing products and history |
| HTML5 | Chat page structure |
| CSS3 | Styling and interface design |
| JavaScript | Sending requests, updating the chat |

---

## 4. Installation Instructions

**Step 1.** Make sure Python is installed:
**Step 2.** Download or unzip the project folder warehouse_chatbot

**Step 3.** Open a terminal in the project folder and install Flask:
---

## 5. How to Run

**Step 1.** Run the application in the terminal:
**Step 2.** Open your browser and go to:
http://127.0.0.1:5000/
**Step 3.** Type a command in the chat field, for example: products or help

---

## 6. Chatbot Usage Examples

**View all products:**
User: products
Bot: 📦 Products in warehouse (10 items):
• Milk 1L — 150 pcs | Dairy House | 85 ₽
• White Bread — 200 pcs | Luxury Bakery | 35 ₽

**Add a new product:**
User: add Cookies 200 CondFactory 45
Bot: ✅ Product Cookies added!
Quantity: 200 pcs, Supplier: CondFactory, Price: 45 ₽

**Stock incoming:**
User: receive Milk 1L 50
Bot: 📥 Stock received!
Product: Milk 1L
Added: +50 pcs. New balance: 200 pcs.

**Stock outgoing:**
User: issue White Bread 30
Bot: 📤 Stock issued!
Product: White Bread
Issued: -30 pcs. Balance: 170 pcs.

**Search for a product:**
User: search milk
Bot: 🔎 Found (1):
• Milk 1L — 200 pcs | Dairy House

**Warehouse report:**
User: report
Bot: 📊 Warehouse Report:
Items: 10 | Units: 2950 | Total value: 199050 ₽
Low stock (less than 50 pcs): 1

**Error — not enough stock:**
User: issue Coffee 999
Bot: ❌ Cannot issue 999 pcs.
Only 60 pcs. in stock.

**Unknown command:**
User: buy milk
Bot: 🤔 Did not understand: «buy milk»
Type help for the list of commands.
---

## 7. Interface Screenshots

![Main page](static/screen1.png)
![Report](static/screen2.png)
![Low stock](static/screen3.png)
---

## Project Structure
warehouse_chatbot/
├── app.py              — main file, Flask + bot logic
├── requirements.txt    — dependencies (flask)
├── README.md           — documentation
├── warehouse.db        — SQLite database (created automatically)
├── templates/
│   └── index.html      — HTML chat page
└── static/
└── style.css       — interface styles

---

## Author

Student: Serikkhanova Aisha
Group: 2502 CS 02
Course: Programming in Python
Topic: Warehouse Catalog — Inventory Management Chatbot