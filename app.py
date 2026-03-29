from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
from collections import Counter
from database import supabase
from ml_utils import predict_all

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
bcrypt = Bcrypt(app)

# Helper function to check login
def is_logged_in():
    return session.get("owner_logged_in", False)

# --- PUBLIC ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit_complaint():
    user_name = request.form.get("user_name")
    complaint_text = request.form.get("complaint_text")

    # Validation
    if not user_name or not complaint_text:
        flash("Name and complaint details are required!", "danger")
        return redirect(url_for("index"))
    
    if len(complaint_text) < 20:
        flash("Complaint must be at least 20 characters long!", "warning")
        return redirect(url_for("index"))

    try:
        # ML Prediction (Combined)
        predicted_topic, predicted_priority, priority_rank = predict_all(complaint_text)

        # Insert into Supabase
        supabase.table("complaints").insert({
            "user_name": user_name,
            "complaint_text": complaint_text,
            "predicted_topic": predicted_topic,
            "predicted_priority": predicted_priority,
            "priority_rank": priority_rank
        }).execute()

        # Automated Triage Response Logic
        if predicted_topic == "Theft/Dispute" and predicted_priority == "High":
            flash("🚨 AUTO-TRIAGE ALERT: We've flagged this as an urgent fraud dispute. Please prepare your transaction IDs. An agent has been notified.", "danger")
        elif predicted_topic == "Unknown / Manual Review Required":
            flash("⚠️ AUTO-TRIAGE ALERT: Your complaint requires manual review by our team. It has been escalated.", "warning")
        else:
            flash("Your complaint has been successfully registered. Thank you for your feedback.", "success")
    except Exception as e:
        flash(f"Error submitting complaint: {str(e)}", "danger")
    
    return redirect(url_for("index"))

# --- OWNER AUTH ROUTES ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            # Fetch owner from Supabase
            response = supabase.table("owner").select("*").eq("username", username).execute()
            
            if response.data and len(response.data) > 0:
                owner = response.data[0]
                if bcrypt.check_password_hash(owner["password"], password):
                    session["owner_logged_in"] = True
                    return redirect(url_for("dashboard"))
            
            flash("Invalid credentials", "danger")
        except Exception as e:
            flash(f"Login error: {str(e)}", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

# --- PROTECTED ROUTES ---

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    try:
        # a. Total count
        total_res = supabase.table("complaints").select("*", count="exact").execute()
        total_count = total_res.count if total_res.count is not None else 0

        # b. All complaints for analytics
        all_res = supabase.table("complaints").select("predicted_priority, predicted_topic").execute()
        priorities = [item["predicted_priority"] for item in all_res.data]
        topics = [item.get("predicted_topic", "N/A") for item in all_res.data]
        
        counts = Counter(priorities)
        topic_counts = Counter(topics)

        # c. Most frequent
        most_frequent = counts.most_common(1)[0][0] if counts else "N/A"
        most_frequent_topic = topic_counts.most_common(1)[0][0] if topic_counts else "N/A"

        # d. Last 5 complaints
        recent_res = supabase.table("complaints").select("*").order("created_at", desc=True).limit(5).execute()
        recent_complaints = recent_res.data

        return render_template("dashboard.html", 
                               total_count=total_count, 
                               counts=counts, 
                               topic_counts=topic_counts,
                               most_frequent=most_frequent,
                               most_frequent_topic=most_frequent_topic,
                               recent_complaints=recent_complaints)
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/complaints")
def complaints_list():
    if not is_logged_in():
        return redirect(url_for("login"))

    priority_filter = request.args.get("priority")
    status_filter = request.args.get("status", "pending")
    
    try:
        query = supabase.table("complaints").select("*").order("priority_rank", desc=False)
        
        if status_filter == "acknowledged":
            query = query.eq("acknowledged", True)
        else:
            query = query.neq("acknowledged", True)
        
        if priority_filter and priority_filter in ["High", "Medium", "Low"]:
            query = query.eq("predicted_priority", priority_filter)
        
        response = query.execute()
        complaints = response.data

        return render_template("complaints.html", complaints=complaints, current_filter=priority_filter, current_status=status_filter)
    except Exception as e:
        flash(f"Error fetching complaints: {str(e)}", "danger")
        return redirect(url_for("dashboard"))

@app.route("/acknowledge/<int:complaint_id>", methods=["POST"])
def acknowledge_complaint(complaint_id):
    if not is_logged_in():
        return {"success": False, "message": "Unauthorized"}, 401
        
    try:
        data = request.get_json()
        new_status = data.get("acknowledged", False)
        
        # Update in Supabase
        supabase.table("complaints").update({"acknowledged": new_status}).eq("id", complaint_id).execute()
        return {"success": True, "acknowledged": new_status}
    except Exception as e:
        return {"success": False, "message": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
