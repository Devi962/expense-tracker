from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import date

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            purpose TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():

    conn = get_db()

    selected_month = request.args.get(
    "month",
    date.today().strftime("%Y-%m")
)
    search = request.args.get("search", "").strip()

    if search:
        expenses = conn.execute(
            """
            SELECT * FROM expenses
            WHERE date LIKE ?
            AND (
                purpose LIKE ?
                OR category LIKE ?
            )
            ORDER BY date DESC, id DESC
            """,
            (
                selected_month + "%",
                "%" + search + "%",
                "%" + search + "%"
            )
        ).fetchall()
    else:
        expenses = conn.execute(
            """
            SELECT * FROM expenses
            WHERE date LIKE ?
            ORDER BY date DESC, id DESC
            """,
            (selected_month + "%",)
        ).fetchall()

    today = date.today().isoformat()

    today_total = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE date = ?
        """,
        (today,)
    ).fetchone()[0]

    monthly_total = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE date LIKE ?
        """,
        (selected_month + "%",)
    ).fetchone()[0]

    category_summary = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE date LIKE ?
        GROUP BY category
        ORDER BY total DESC
        """,
        (selected_month + "%",)
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        expenses=expenses,
        today_total=today_total,
        monthly_total=monthly_total,
        category_summary=category_summary,
        selected_month=selected_month,
        search=search
    )


@app.route("/add", methods=["POST"])
def add_expense():

    expense_date = request.form["date"]
    purpose = request.form["purpose"]
    category = request.form["category"]
    amount = request.form["amount"]

    conn = get_db()

    conn.execute(
        """
        INSERT INTO expenses (date, purpose, category, amount)
        VALUES (?, ?, ?, ?)
        """,
        (expense_date, purpose, category, amount)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):

    conn = get_db()

    if request.method == "POST":

        expense_date = request.form["date"]
        purpose = request.form["purpose"]
        category = request.form["category"]
        amount = request.form["amount"]

        conn.execute(
            """
            UPDATE expenses
            SET date = ?, purpose = ?, category = ?, amount = ?
            WHERE id = ?
            """,
            (expense_date, purpose, category, amount, expense_id)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ?",
        (expense_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit.html",
        expense=expense
    )


create_table()

if __name__ == "__main__":
    app.run(debug=True)
