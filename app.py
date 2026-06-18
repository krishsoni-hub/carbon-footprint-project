import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from config import Config
from models.database import db, User, CarbonLog, UserGoal, CarbonMetric
from controllers.calculator import calculate_footprint
from controllers.ai_assistant import extract_metrics_from_chat
from controllers.recommendations import get_contextual_advice

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Bind SQLAlchemy database instance with application configurations
db.init_app(app)

# Ensure database tables are created on initialization and seed dummy data
with app.app_context():
    db.create_all()
    # Ensure active dummy user with ID 1 exists for sandbox sessions
    dummy_user = User.query.get(1)
    if not dummy_user:
        dummy_user = User(id=1, username="eco_pioneer")
        db.session.add(dummy_user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

@app.route('/')
def index():
    """Render the main index dashboard view with historical averages and metrics list."""
    try:
        # Fetch the latest 10 CarbonLog rows for user_id 1
        logs = CarbonLog.query.filter_by(user_id=1).order_by(CarbonLog.timestamp.desc()).limit(10).all()
        logs_list = [log.to_dict() for log in logs]
        
        # Calculate historical averages
        total_logs = len(logs)
        if total_logs > 0:
            avg_total = sum(l.total_emissions for l in logs) / total_logs
            avg_transport = sum(l.transport_emissions for l in logs) / total_logs
            avg_energy = sum(l.energy_emissions for l in logs) / total_logs
            avg_diet = sum(l.diet_emissions for l in logs) / total_logs
        else:
            avg_total = 0.0
            avg_transport = 0.0
            avg_energy = 0.0
            avg_diet = 0.0
            
        averages = {
            "total": round(avg_total, 2),
            "transport": round(avg_transport, 2),
            "energy": round(avg_energy, 2),
            "diet": round(avg_diet, 2)
        }

        # Query standard category metrics for simple visualizers
        metrics = CarbonMetric.query.all()
        metrics_list = [m.to_dict() for m in metrics]

        return render_template(
            "index.html", 
            logs=logs_list, 
            averages=averages, 
            metrics=metrics_list
        )
    except Exception:
        # Prevent database lockouts or exceptions from crashing dashboard render
        return render_template(
            "index.html",
            logs=[],
            averages={"total": 0.0, "transport": 0.0, "energy": 0.0, "diet": 0.0},
            metrics=[]
        )

@app.route('/chat')
def chat_view():
    """Render the interactive AI assistant view."""
    return render_template("chat.html")

@app.route('/api/chat', methods=['POST'])
def chat():
    """POST endpoint handling natural language carbon logging activity parsing and scoring."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({
            "error": "Bad Request",
            "message": "Missing 'message' key in JSON payload."
        }), 400
    
    user_message = data['message']
    api_key = app.config.get("GEMINI_API_KEY")
    
    try:
        # 1. Query AI extraction parsing outputs
        parsed_metrics = extract_metrics_from_chat(user_message, api_key)
        
        # 2. Run algorithmic conversion calculations
        emissions_breakdown = calculate_footprint(parsed_metrics)
        
        # 3. Create database logger row
        carbon_log = CarbonLog(
            user_id=1,
            transport_emissions=emissions_breakdown["transport_emissions"],
            energy_emissions=emissions_breakdown["energy_emissions"],
            diet_emissions=emissions_breakdown["diet_emissions"],
            total_emissions=emissions_breakdown["total_emissions"],
            source_text=user_message
        )
        
        # Update generalized metrics by category for dashboard widgets
        for category_name, val in [
            ("transport", carbon_log.transport_emissions),
            ("energy", carbon_log.energy_emissions),
            ("diet", carbon_log.diet_emissions)
        ]:
            metric = CarbonMetric.query.filter_by(category=category_name).first()
            if metric:
                metric.value = val
            else:
                metric = CarbonMetric(category=category_name, value=val, unit="kg")
                db.session.add(metric)
        
        db.session.add(carbon_log)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal Server Error",
            "message": f"Database transaction commit failed: {str(e)}"
        }), 500
        
    # 4. Generate recommendation response
    recommendations = get_contextual_advice(emissions_breakdown)
    
    # 5. Return fully formatted results
    return jsonify({
        "user_message": user_message,
        "parsed_metrics": parsed_metrics,
        "emissions_breakdown": emissions_breakdown,
        "recommendations": recommendations,
        "carbon_log_id": carbon_log.id
    }), 200

@app.route('/api/log', methods=['POST'])
def log_metric():
    """POST endpoint for saving or overwriting manual carbon metrics in database."""
    data = request.get_json()
    if not data:
        return jsonify({
            "error": "Bad Request",
            "message": "Missing JSON payload."
        }), 400
    
    category = data.get("category")
    value = data.get("value")
    unit = data.get("unit", "kg")
    
    if not category or value is None:
        return jsonify({
            "error": "Bad Request",
            "message": "Both 'category' and 'value' fields are required."
        }), 400
        
    try:
        metric = CarbonMetric.query.filter_by(category=category).first()
        if metric:
            metric.value = float(value)
            if "unit" in data:
                metric.unit = data["unit"]
        else:
            metric = CarbonMetric(category=category, value=float(value), unit=unit)
            db.session.add(metric)
            
        db.session.commit()
        return jsonify({
            "success": True,
            "metric": metric.to_dict()
        }), 200
    except ValueError:
        return jsonify({
            "error": "Bad Request",
            "message": "Carbon metric value must be a valid float/number."
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Internal Server Error",
            "message": f"Database error encountered: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """JSON error handler for page/route not found (HTTP 404)."""
    return jsonify({
        "error": "Not Found",
        "message": "The requested URL or resource was not found on this server."
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """JSON error handler for internal server errors (HTTP 500)."""
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected server error occurred. Please try again later."
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
