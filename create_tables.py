import sqlite3

# データベース接続
conn = sqlite3.connect('cafe_app.db')
c = conn.cursor()

# テーブル作成 SQL
c.execute('''
CREATE TABLE IF NOT EXISTS PRODUCTS (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME TEXT NOT NULL,
    DESCRIPTION TEXT NOT NULL,
    CATEGORY TEXT NOT NULL,
    PRICE REAL NOT NULL
)
''')

# コミットして接続を閉じる
conn.commit()
conn.close()

print("テーブルが作成されました。")
