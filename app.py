from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # フラッシュメッセージ用のシークレットキー

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # フォームデータを取得
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        price = request.form['price']

        # データベースに接続
        conn = sqlite3.connect('cafe_app.db')
        c = conn.cursor()

        # 商品をデータベースに挿入
        c.execute('INSERT INTO PRODUCTS (NAME, DESCRIPTION, CATEGORY, PRICE) VALUES (?, ?, ?, ?)', 
                  (name, description, category, price))

        # 変更をコミットしてデータベースを保存
        conn.commit()
        conn.close()

        # 成功メッセージを表示
        flash('商品が正常に登録されました。')
        return redirect(url_for('add_product'))

    return render_template('add_product.html')

if __name__ == '__main__':
    app.run(debug=True)
