from uuid import uuid4
from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://postgres:Rksd2005@localhost:5432/savings_app"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")  # Load the secret key from .env

db = SQLAlchemy(app)


# Database Model
class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String, nullable=False)  # User-specific identifier
    name = db.Column(db.String, nullable=False)
    goal = db.Column(db.Float, nullable=False)
    current_savings = db.Column(db.Float, nullable=False)
    remaining = db.Column(db.Float, nullable=False)
    monthly_savings = db.Column(db.Float, nullable=False)
    monthly_income = db.Column(db.Float, nullable=False)
    progress = db.Column(db.Float, nullable=False)
    months = db.Column(db.Float, nullable=False)
    savings_rate = db.Column(db.Float, nullable=False)


# Create database tables
with app.app_context():
    db.create_all()


def update_overall_metrics(user_id):
    """Recalculate overall metrics for a specific user."""
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    total_goal = sum(goal.goal for goal in goals)
    total_current_savings = sum(goal.current_savings for goal in goals)
    total_monthly_savings = sum(goal.monthly_savings for goal in goals)
    remaining = total_goal - total_current_savings
    progress = (total_current_savings / total_goal) * 100 if total_goal > 0 else 0
    months = (
        remaining / total_monthly_savings if total_monthly_savings > 0 else float("inf")
    )

    session["overall_metrics"] = {
        "total_goal": total_goal,
        "total_current_savings": total_current_savings,
        "total_monthly_savings": total_monthly_savings,
        "remaining": remaining,
        "progress": round(progress, 2),
        "months": round(months, 2),
    }


@app.route("/")
def index():
    # Check if user has a session
    if "user_id" not in session:
        session["user_id"] = str(uuid4())  # Create a new session for the user
        session["overall_metrics"] = {
            "total_goal": 0,
            "total_current_savings": 0,
            "total_monthly_savings": 0,
            "remaining": 0,
            "progress": 0,
            "months": 0,
        }
    return render_template("index.html", overall=session["overall_metrics"])


@app.route("/calculate", methods=["POST"])
def calculate():
    goal = float(request.form["goal"])
    monthly_savings = float(request.form["monthly_savings"])
    current_savings = float(request.form["current_savings"])
    monthly_income = float(request.form["monthly_income"])

    remaining = goal - current_savings
    months = remaining / monthly_savings if monthly_savings > 0 else float("inf")
    progress = (current_savings / goal) * 100 if goal > 0 else 0
    savings_rate = (monthly_savings / monthly_income) * 100 if monthly_income > 0 else 0

    return render_template(
        "result.html",
        goal=goal,
        current_savings=current_savings,
        remaining=remaining,
        months=round(months, 2),
        progress=round(progress, 2),
        savings_rate=round(savings_rate, 2),
    )


@app.route("/add_goal", methods=["POST"])
def add_goal():
    user_id = session.get("user_id")
    goal_name = request.form["goal_name"]
    goal = float(request.form["goal"])
    monthly_savings = float(request.form["monthly_savings"])
    current_savings = float(request.form["current_savings"])
    monthly_income = float(request.form["monthly_income"])

    remaining = goal - current_savings
    progress = (current_savings / goal) * 100 if goal > 0 else 0
    months = (remaining / monthly_savings) if monthly_savings > 0 else float("inf")
    savings_rate = (monthly_savings / monthly_income) * 100 if monthly_income > 0 else 0

    new_goal = SavingsGoal(
        id=str(uuid4()),
        user_id=user_id,
        name=goal_name,
        goal=goal,
        current_savings=current_savings,
        remaining=remaining,
        monthly_savings=monthly_savings,
        monthly_income=monthly_income,
        progress=round(progress, 2),
        months=round(months, 2),
        savings_rate=round(savings_rate, 2),
    )
    db.session.add(new_goal)
    db.session.commit()

    update_overall_metrics(user_id)  # Update metrics for this user
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")  # Redirect to index if no session
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    return render_template(
        "dashboard.html", goals=goals, overall=session["overall_metrics"]
    )


@app.route("/delete_goal", methods=["POST"])
def delete_goal():
    user_id = session.get("user_id")
    goal_id = request.form["goal_id"]
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first()
    if goal:
        db.session.delete(goal)
        db.session.commit()

    update_overall_metrics(user_id)  # Update metrics for this user
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(debug=True)
