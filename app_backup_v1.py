from flask import Flask, request, redirect, render_template_string
import sqlite3

app = Flask(__name__)

ADMIN_PASSWORD = "CNBB2026"
DB = "checklist.db"

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>部活チェックリスト</title>
<style>
body{font-family:sans-serif;max-width:900px;margin:auto;padding:20px}
.card{border:1px solid #ddd;border-radius:10px;padding:15px;margin:10px 0}
input[type=text],input[type=password]{width:100%;padding:8px;margin:5px 0;box-sizing:border-box}
button{padding:8px 12px}
a{text-decoration:none}
</style>
</head>
<body>
<h1>共有チェックリスト</h1>

<div class="card">
<h2>チェックリスト一覧</h2>
<ul>
{% for l in lists %}
<li><a href="/list/{{l[0]}}">{{l[1]}}</a></li>
{% endfor %}
</ul>
</div>

<div class="card">
<h2>管理者：新規リスト作成</h2>
<form method="post" action="/create_list">
<input type="password" name="password" placeholder="管理者パスワード">
<input type="text" name="name" placeholder="例: 文化祭">
<button>作成</button>
</form>
</div>
</body>
</html>
"""

LIST_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{name}}</title>
<style>
body{font-family:sans-serif;max-width:900px;margin:auto;padding:20px}
.card{border:1px solid #ddd;border-radius:10px;padding:15px;margin:10px 0}
.row{display:flex;justify-content:space-between;gap:10px;align-items:center}
input[type=text],input[type=password]{width:100%;padding:8px;margin:5px 0;box-sizing:border-box}
button{padding:8px 12px}
</style>
</head>
<body>
<a href="/">← 戻る</a>
<h1>{{name}}</h1>

<div class="card">
{% for item in items %}
<div class="row">
<form method="post" action="/toggle">
<input type="hidden" name="id" value="{{item[0]}}">
<label>
<input type="checkbox" onchange="this.form.submit()" {% if item[3] %}checked{% endif %}>
{{item[2]}}
</label>
</form>

<form method="post" action="/delete_item">
<input type="hidden" name="id" value="{{item[0]}}">
<input type="password" name="password" placeholder="管理者PW">
<button>項目削除</button>
</form>
</div>
<hr>
{% endfor %}
</div>

<div class="card">
<h2>項目追加</h2>
<form method="post" action="/add_item">
<input type="hidden" name="list_id" value="{{list_id}}">
<input type="password" name="password" placeholder="管理者パスワード">
<input type="text" name="text" placeholder="新しい項目">
<button>追加</button>
</form>
</div>

<div class="card">
<h2>チェックリスト削除</h2>
<form method="post" action="/delete_list">
<input type="hidden" name="list_id" value="{{list_id}}">
<input type="password" name="password" placeholder="管理者パスワード">
<button>このリストを削除</button>
</form>
</div>

</body>
</html>
"""

def db():
    return sqlite3.connect(DB)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS lists(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL)")
    cur.execute("""CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER,
        text TEXT NOT NULL,
        checked INTEGER DEFAULT 0)""")
    con.commit()
    con.close()

@app.route("/")
def home():
    con = db()
    lists = con.execute("SELECT * FROM lists ORDER BY id DESC").fetchall()
    con.close()
    return render_template_string(HTML, lists=lists)

@app.route("/create_list", methods=["POST"])
def create_list():
    if request.form["password"] != ADMIN_PASSWORD:
        return "パスワードが違います"
    name = request.form["name"].strip()
    if name:
        con = db()
        con.execute("INSERT INTO lists(name) VALUES(?)", (name,))
        con.commit()
        con.close()
    return redirect("/")

@app.route("/list/<int:list_id>")
def show_list(list_id):
    con = db()
    row = con.execute("SELECT name FROM lists WHERE id=?", (list_id,)).fetchone()
    if not row:
        con.close()
        return "見つかりません"
    items = con.execute("SELECT * FROM items WHERE list_id=? ORDER BY id", (list_id,)).fetchall()
    con.close()
    return render_template_string(LIST_HTML, name=row[0], items=items, list_id=list_id)

@app.route("/toggle", methods=["POST"])
def toggle():
    item_id = request.form["id"]
    con = db()
    con.execute("UPDATE items SET checked = CASE WHEN checked=0 THEN 1 ELSE 0 END WHERE id=?", (item_id,))
    con.commit()
    list_id = con.execute("SELECT list_id FROM items WHERE id=?", (item_id,)).fetchone()[0]
    con.close()
    return redirect(f"/list/{list_id}")

@app.route("/add_item", methods=["POST"])
def add_item():
    if request.form["password"] != ADMIN_PASSWORD:
        return "パスワードが違います"
    list_id = request.form["list_id"]
    text = request.form["text"].strip()
    if text:
        con = db()
        con.execute("INSERT INTO items(list_id,text) VALUES(?,?)", (list_id, text))
        con.commit()
        con.close()
    return redirect(f"/list/{list_id}")

@app.route("/delete_item", methods=["POST"])
def delete_item():
    if request.form["password"] != ADMIN_PASSWORD:
        return "パスワードが違います"
    item_id = request.form["id"]
    con = db()
    row = con.execute("SELECT list_id FROM items WHERE id=?", (item_id,)).fetchone()
    if row:
        list_id = row[0]
        con.execute("DELETE FROM items WHERE id=?", (item_id,))
        con.commit()
        con.close()
        return redirect(f"/list/{list_id}")
    con.close()
    return redirect("/")

@app.route("/delete_list", methods=["POST"])
def delete_list():
    if request.form["password"] != ADMIN_PASSWORD:
        return "パスワードが違います"
    list_id = request.form["list_id"]
    con = db()
    con.execute("DELETE FROM items WHERE list_id=?", (list_id,))
    con.execute("DELETE FROM lists WHERE id=?", (list_id,))
    con.commit()
    con.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
