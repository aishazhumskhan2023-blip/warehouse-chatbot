from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("warehouse.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            supplier TEXT,
            price    REAL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            action  TEXT,
            product TEXT,
            amount  INTEGER,
            date    TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            text   TEXT,
            time   TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        test_data = [
            ("Milk 1L",        150, "Dairy House",     85),
            ("White Bread",    200, "Luxury Bakery",   35),
            ("Apples 1kg",     300, "FarmAgro",        90),
            ("Sugar 1kg",      500, "AgroProd",        65),
            ("Buckwheat 1kg",  400, "AgroProd",        75),
            ("Green Tea",      120, "TeaTrade",       180),
            ("Coffee",          60, "BeverageImport", 350),
            ("Pasta",          350, "AgroProd",        55),
            ("Water 2L",       250, "AquaPure",        45),
            ("Salt 1kg",       600, "SaltProm",        25),
        ]
        for name, qty, supplier, price in test_data:
            conn.execute(
                "INSERT INTO products (name, quantity, supplier, price) VALUES (?, ?, ?, ?)",
                (name, qty, supplier, price)
            )
    conn.commit()
    conn.close()


create_tables()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"reply": "Error: empty request", "type": "error"})

        message = data["message"].strip()

        if message == "":
            return jsonify({"reply": "⚠️ You didn't type anything. Enter a command.", "type": "warning"})

        conn = get_db()
        conn.execute("INSERT INTO messages (sender, text) VALUES (?, ?)", ("user", message))
        conn.commit()
        conn.close()

        reply, msg_type = get_bot_reply(message)

        conn = get_db()
        conn.execute("INSERT INTO messages (sender, text) VALUES (?, ?)", ("bot", reply))
        conn.commit()
        conn.close()

        return jsonify({"reply": reply, "type": msg_type})

    except Exception as e:
        return jsonify({"reply": f"❌ Server error: {str(e)}", "type": "error"})


def get_bot_reply(message):
    msg = message.lower().strip()
    conn = get_db()

    if "hello" in msg or "hi" in msg or "hey" in msg:
        conn.close()
        return (
            "👋 Hello! I am WarehouseBot.<br>"
            "Type <b>help</b> to see all available commands.",
            "info"
        )

    if "help" in msg or "commands" in msg:
        conn.close()
        return (
            "📋 <b>Command list:</b><br><br>"
            "• <b>products</b> — all products in warehouse<br>"
            "• <b>add [name] [qty] [supplier] [price]</b> — add product<br>"
            "• <b>receive [name] [qty]</b> — add incoming stock<br>"
            "• <b>issue [name] [qty]</b> — write off stock<br>"
            "• <b>stock [name]</b> — check product balance<br>"
            "• <b>search [word]</b> — search for a product<br>"
            "• <b>suppliers</b> — list of suppliers<br>"
            "• <b>report</b> — full warehouse report<br>"
            "• <b>history</b> — last operations<br>"
            "• <b>low</b> — low stock products<br>"
            "• <b>delete [name]</b> — delete product<br>"
            "• <b>stats</b> — general statistics<br>"
            "• <b>clear</b> — clear chat history<br>",
            "info"
        )

    if msg in ["products", "warehouse", "list", "all products"]:
        rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        conn.close()
        if not rows:
            return "Warehouse is empty. Add products first.", "info"
        result = f"📦 <b>Products in warehouse ({len(rows)} items):</b><br>"
        for row in rows:
            result += f"• <b>{row['name']}</b> — {row['quantity']} pcs | {row['supplier']} | {row['price']} ₽<br>"
        return result, "info"

    if msg.startswith("add "):
        parts = message.split()
        if len(parts) < 5:
            conn.close()
            return "❌ Wrong format. Example: <b>add Sugar 100 AgroProd 65</b>", "error"
        try:
            price    = float(parts[-1])
            supplier = parts[-2]
            quantity = int(parts[-3])
            name     = " ".join(parts[1:-3])
        except ValueError:
            conn.close()
            return "❌ Error. Make sure quantity and price are numbers.", "error"

        existing = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        if existing:
            conn.close()
            return f"⚠️ Product <b>{name}</b> already exists. Use <b>receive</b> to restock.", "warning"

        conn.execute(
            "INSERT INTO products (name, quantity, supplier, price) VALUES (?, ?, ?, ?)",
            (name, quantity, supplier, price)
        )
        conn.execute(
            "INSERT INTO history (action, product, amount) VALUES (?, ?, ?)",
            ("Added", name, quantity)
        )
        conn.commit()
        conn.close()
        return (
            f"✅ Product <b>{name}</b> added!<br>"
            f"Quantity: {quantity} pcs, Supplier: {supplier}, Price: {price} ₽",
            "success"
        )

    if msg.startswith("receive "):
        parts = message.split()
        if len(parts) < 3:
            conn.close()
            return "❌ Format: <b>receive Milk 50</b>", "error"
        try:
            qty  = int(parts[-1])
            name = " ".join(parts[1:-1])
        except ValueError:
            conn.close()
            return "❌ Quantity must be a number.", "error"

        product = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        if not product:
            conn.close()
            return f"❌ Product <b>{name}</b> not found. Add it first.", "error"

        new_qty = product["quantity"] + qty
        conn.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, product["id"]))
        conn.execute(
            "INSERT INTO history (action, product, amount) VALUES (?, ?, ?)",
            ("Received", product["name"], qty)
        )
        conn.commit()
        conn.close()
        return (
            f"📥 Stock received!<br>"
            f"Product: <b>{product['name']}</b><br>"
            f"Added: +{qty} pcs. New balance: <b>{new_qty} pcs.</b>",
            "success"
        )

    if msg.startswith("issue "):
        parts = message.split()
        if len(parts) < 3:
            conn.close()
            return "❌ Format: <b>issue Milk 10</b>", "error"
        try:
            qty  = int(parts[-1])
            name = " ".join(parts[1:-1])
        except ValueError:
            conn.close()
            return "❌ Quantity must be a number.", "error"

        product = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        if not product:
            conn.close()
            return f"❌ Product <b>{name}</b> not found.", "error"

        if product["quantity"] < qty:
            conn.close()
            return (
                f"❌ Cannot issue {qty} pcs.<br>"
                f"Only <b>{product['quantity']} pcs.</b> in stock.",
                "error"
            )

        new_qty = product["quantity"] - qty
        conn.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, product["id"]))
        conn.execute(
            "INSERT INTO history (action, product, amount) VALUES (?, ?, ?)",
            ("Issued", product["name"], qty)
        )
        conn.commit()
        conn.close()

        reply = (
            f"📤 Stock issued!<br>"
            f"Product: <b>{product['name']}</b><br>"
            f"Issued: -{qty} pcs. Balance: <b>{new_qty} pcs.</b>"
        )
        if new_qty <= 20:
            reply += f"<br>⚠️ Warning! Low stock: {new_qty} pcs."
        return reply, "success"

    if msg.startswith("stock "):
        name    = message[6:].strip()
        product = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        conn.close()
        if not product:
            return f"❌ Product <b>{name}</b> not found. Try <b>search {name}</b>", "error"

        qty = product["quantity"]
        if qty == 0:
            status = "🔴 out of stock"
        elif qty < 50:
            status = "🟡 low"
        else:
            status = "🟢 sufficient"

        return (
            f"🔍 <b>{product['name']}</b><br>"
            f"Balance: <b>{qty} pcs.</b> — {status}<br>"
            f"Supplier: {product['supplier']}<br>"
            f"Price: {product['price']} ₽",
            "info"
        )

    if msg.startswith("search "):
        query = message[7:].strip().lower()
        rows  = conn.execute("SELECT * FROM products").fetchall()
        conn.close()
        found = [r for r in rows if query in r["name"].lower() or query in (r["supplier"] or "").lower()]
        if not found:
            return f"🔎 Nothing found for <b>«{query}»</b>", "warning"
        result = f"🔎 <b>Found ({len(found)}):</b><br>"
        for r in found:
            result += f"• <b>{r['name']}</b> — {r['quantity']} pcs | {r['supplier']}<br>"
        return result, "info"

    if msg in ["suppliers"]:
        rows = conn.execute(
            "SELECT supplier, COUNT(*) as cnt, SUM(quantity) as total "
            "FROM products GROUP BY supplier ORDER BY supplier"
        ).fetchall()
        conn.close()
        if not rows:
            return "No suppliers found.", "info"
        result = "🏭 <b>Suppliers:</b><br>"
        for r in rows:
            result += f"• <b>{r['supplier']}</b> — {r['cnt']} product(s), {r['total']} pcs.<br>"
        return result, "info"

    if msg in ["report"]:
        rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        conn.close()
        if not rows:
            return "Warehouse is empty.", "info"
        total_items = sum(r["quantity"] for r in rows)
        total_value = sum(r["quantity"] * r["price"] for r in rows)
        low         = [r for r in rows if r["quantity"] < 50]

        result  = "📊 <b>Warehouse Report:</b><br>"
        result += f"Items: <b>{len(rows)}</b> | Units: <b>{total_items}</b> | Total value: <b>{total_value:.0f} ₽</b><br>"
        result += f"Low stock (less than 50 pcs): <b>{len(low)}</b><br><br>"
        result += "<b>All products:</b><br>"
        for r in rows:
            icon = "🔴" if r["quantity"] == 0 else ("🟡" if r["quantity"] < 50 else "🟢")
            result += f"{icon} <b>{r['name']}</b> — {r['quantity']} pcs × {r['price']} ₽<br>"
        return result, "info"

    if msg in ["history", "operations", "log"]:
        rows = conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT 15").fetchall()
        conn.close()
        if not rows:
            return "Operation history is empty.", "info"
        result = "📋 <b>Last operations:</b><br>"
        for r in rows:
            icon = "📥" if r["action"] == "Received" else ("📤" if r["action"] == "Issued" else "➕")
            result += f"{icon} {r['action']} — <b>{r['product']}</b> {r['amount']} pcs ({r['date'][:16]})<br>"
        return result, "info"

    if msg in ["low", "low stock"]:
        rows = conn.execute(
            "SELECT * FROM products WHERE quantity < 50 ORDER BY quantity"
        ).fetchall()
        conn.close()
        if not rows:
            return "✅ All products have sufficient stock.", "success"
        result = f"⚠️ <b>Low stock products ({len(rows)}):</b><br>"
        for r in rows:
            icon = "🔴" if r["quantity"] == 0 else "🟡"
            result += f"{icon} <b>{r['name']}</b> — {r['quantity']} pcs.<br>"
        return result, "warning"

    if msg.startswith("delete "):
        name    = message[7:].strip()
        product = conn.execute(
            "SELECT * FROM products WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        if not product:
            conn.close()
            return f"❌ Product <b>{name}</b> not found.", "error"
        conn.execute("DELETE FROM products WHERE id = ?", (product["id"],))
        conn.commit()
        conn.close()
        return f"🗑️ Product <b>{product['name']}</b> deleted from warehouse.", "success"

    if msg in ["stats", "statistics"]:
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt, SUM(quantity) as units, SUM(quantity*price) as value FROM products"
            ).fetchone()
            suppliers = conn.execute(
                "SELECT COUNT(DISTINCT supplier) as s FROM products"
            ).fetchone()
            conn.close()
            cnt   = row["cnt"]   if row["cnt"]   else 0
            units = row["units"] if row["units"] else 0
            value = row["value"] if row["value"] else 0
            s     = suppliers["s"] if suppliers["s"] else 0
            return (
                f"📈 <b>Warehouse Statistics:</b><br>"
                f"Total items: <b>{cnt}</b><br>"
                f"Total units: <b>{units}</b><br>"
                f"Total value: <b>{value:.0f} ₽</b><br>"
                f"Suppliers: <b>{s}</b>",
                "info"
            )
        except Exception as e:
            conn.close()
            return f"❌ Error getting statistics: {str(e)}", "error"

    if msg in ["clear", "clear history"]:
        conn.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
        return "🧹 Chat history cleared.", "info"

    if "who are you" in msg or "what are you" in msg or "about" in msg:
        conn.close()
        return (
            "🤖 I am WarehouseBot!<br>"
            "I help manage warehouse inventory.<br>"
            "Built with Python + Flask + SQLite.<br>"
            "Type <b>help</b> for the list of commands.",
            "info"
        )

    conn.close()
    return (
        f"🤔 Did not understand: <b>«{message}»</b><br>"
        f"Type <b>help</b> for the list of commands.",
        "warning"
    )


if __name__ == "__main__":
    print("Server running: http://127.0.0.1:5000")
    app.run(debug=True)