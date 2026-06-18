"""Main Flask application configuration and routing endpoints.

This module initializes the Flask server with database connections, seeds dummy
users, configures system-wide logging, and sets up dashboard rendering and
JSON REST APIs for carbon footprint tracking and analysis.
"""

import logging
import os
from typing import Any, Dict, Generator, List, Tuple, Union

from flask import Flask, Response, jsonify, render_template, request
from sqlalchemy.orm import load_only

from config import Config
from controllers.ai_assistant import extract_metrics_from_chat
from controllers.calculator import calculate_footprint
from controllers.recommendations import get_contextual_advice
from models.database import CarbonLog, CarbonMetric, User, db

# Configure system-wide enterprise logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Bind SQLAlchemy database instance with application configurations
db.init_app(app)


def stream_carbon_logs(
    user_id: int, chunk_size: int = 10
) -> Generator[CarbonLog, None, None]:
    """Streams carbon log records using explicit limit-offset chunked pagination.

    This generator utilizes SQLAlchemy's load_only options to retrieve only the
    necessary columns, minimizing memory footprint and database query runtime.

    Args:
        user_id (int): Unique identifier of the user.
        chunk_size (int): The number of rows loaded per database trip. Defaults to 10.

    Yields:
        Generator[CarbonLog, None, None]: Generator yielding individual CarbonLog instances.

    Raises:
        Exception: If database connection or query fails.
    """
    offset: int = 0
    while True:
        chunk: List[CarbonLog] = (
            db.session.query(CarbonLog)
            .filter_by(user_id=user_id)
            .options(
                load_only(
                    CarbonLog.id,
                    CarbonLog.timestamp,
                    CarbonLog.transport_emissions,
                    CarbonLog.energy_emissions,
                    CarbonLog.diet_emissions,
                    CarbonLog.total_emissions,
                    CarbonLog.source_text,
                )
            )
            .order_by(CarbonLog.timestamp.desc())
            .limit(chunk_size)
            .offset(offset)
            .all()
        )
        if not chunk:
            break
        for log in chunk:
            yield log
        offset += chunk_size


# Ensure database tables are created on initialization and seed dummy data
with app.app_context():
    db.create_all()
    # Ensure active dummy user with ID 1 exists for sandbox sessions
    dummy_user: Union[User, None] = db.session.get(User, 1)
    if not dummy_user:
        dummy_user = User(id=1, username="eco_pioneer")
        db.session.add(dummy_user)
        try:
            db.session.commit()
            logger.info("Successfully seeded default dummy user 'eco_pioneer' into database.")
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to seed dummy user during startup: {str(e)}",
                exc_info=True,
            )


@app.route('/')
def index() -> str:
    """Render the main index dashboard view with historical averages and metrics list.

    Returns:
        str: Rendered HTML template string for the dashboard view.

    Raises:
        Exception: If template rendering or queries fail.
    """
    try:
        logger.info("Transitioning to dashboard index view.")

        # Load logs efficiently using the paginated generator, limited to 10 rows
        logs_generator: Generator[CarbonLog, None, None] = stream_carbon_logs(
            user_id=1, chunk_size=10
        )
        logs: List[CarbonLog] = []
        for _ in range(10):
            try:
                logs.append(next(logs_generator))
            except StopIteration:
                break

        logs_list: List[Dict[str, Any]] = [
            {
                "id": log.id,
                "user_id": 1,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "transport_emissions": log.transport_emissions,
                "energy_emissions": log.energy_emissions,
                "diet_emissions": log.diet_emissions,
                "total_emissions": log.total_emissions,
                "source_text": log.source_text
            }
            for log in logs
        ]

        # Calculate historical averages from the retrieved chunk
        total_logs: int = len(logs)
        if total_logs > 0:
            avg_total: float = sum(l.total_emissions for l in logs) / total_logs
            avg_transport: float = (
                sum(l.transport_emissions for l in logs) / total_logs
            )
            avg_energy: float = sum(l.energy_emissions for l in logs) / total_logs
            avg_diet: float = sum(l.diet_emissions for l in logs) / total_logs
        else:
            avg_total = 0.0
            avg_transport = 0.0
            avg_energy = 0.0
            avg_diet = 0.0

        averages: Dict[str, float] = {
            "total": round(avg_total, 2),
            "transport": round(avg_transport, 2),
            "energy": round(avg_energy, 2),
            "diet": round(avg_diet, 2),
        }

        # Query standard category metrics for simple visualizers utilizing load_only optimization
        metrics: List[CarbonMetric] = (
            db.session.query(CarbonMetric)
            .options(
                load_only(
                    CarbonMetric.id,
                    CarbonMetric.category,
                    CarbonMetric.value,
                    CarbonMetric.unit,
                )
            )
            .all()
        )
        metrics_list: List[Dict[str, Any]] = [m.to_dict() for m in metrics]

        return render_template(
            "index.html",
            logs=logs_list,
            averages=averages,
            metrics=metrics_list,
        )
    except Exception as e:
        logger.error(
            f"Error occurred while loading dashboard index: {str(e)}",
            exc_info=True,
        )
        return render_template(
            "index.html",
            logs=[],
            averages={
                "total": 0.0,
                "transport": 0.0,
                "energy": 0.0,
                "diet": 0.0,
            },
            metrics=[],
        )


@app.route('/chat')
def chat_view() -> str:
    """Render the interactive AI assistant view.

    Returns:
        str: Rendered HTML template string for the chat view.

    Raises:
        Exception: If rendering the template fails.
    """
    logger.info("Transitioning to chat dashboard view.")
    return render_template("chat.html")


@app.route('/api/chat', methods=['POST'])
def chat() -> Tuple[Response, int]:
    """POST endpoint handling natural language carbon logging activity parsing and scoring.

    Returns:
        Tuple[Response, int]: A tuple containing the JSON response and the HTTP status code.

    Raises:
        Exception: If database execution or parsing fails.
    """
    logger.info("Received request on API chat endpoint.")
    data: Any = request.get_json()
    if not data or "message" not in data or not str(data["message"]).strip():
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Missing or empty 'message' key in JSON payload.",
                }
            ),
            400,
        )

    user_message: str = data["message"]
    api_key: Union[str, None] = app.config.get("GEMINI_API_KEY")

    try:
        # 1. Query AI extraction parsing outputs
        parsed_metrics: Dict[str, Any] = extract_metrics_from_chat(
            user_message, api_key
        )

        # 2. Run algorithmic conversion calculations
        emissions_breakdown: Dict[str, float] = calculate_footprint(
            parsed_metrics
        )

        # Log warning if calculations exceed the anomalous high emission threshold (> 20.0 kg CO2)
        if emissions_breakdown["total_emissions"] > 20.0:
            logger.warning(
                f"Anomalous high carbon footprint detected: {emissions_breakdown['total_emissions']} kg CO2. "
                f"Breakdown: [Transport: {emissions_breakdown['transport_emissions']} kg CO2, "
                f"Energy: {emissions_breakdown['energy_emissions']} kg CO2, "
                f"Diet: {emissions_breakdown['diet_emissions']} kg CO2]"
            )

        # 3. Create database logger row
        carbon_log: CarbonLog = CarbonLog(
            user_id=1,
            transport_emissions=emissions_breakdown["transport_emissions"],
            energy_emissions=emissions_breakdown["energy_emissions"],
            diet_emissions=emissions_breakdown["diet_emissions"],
            total_emissions=emissions_breakdown["total_emissions"],
            source_text=user_message,
        )

        # Update generalized metrics by category for dashboard widgets
        for category_name, val in [
            ("transport", carbon_log.transport_emissions),
            ("energy", carbon_log.energy_emissions),
            ("diet", carbon_log.diet_emissions),
        ]:
            metric: Union[CarbonMetric, None] = (
                db.session.query(CarbonMetric)
                .filter_by(category=category_name)
                .first()
            )
            if metric:
                metric.value = val
            else:
                metric = CarbonMetric(
                    category=category_name, value=val, unit="kg"
                )
                db.session.add(metric)

        db.session.add(carbon_log)
        db.session.commit()
        logger.info(
            f"Successfully logged emissions record and updated category metrics (Log ID: {carbon_log.id})."
        )

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to commit carbon log record to database: {str(e)}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Database transaction commit failed: {str(e)}",
                }
            ),
            500,
        )

    # 4. Generate recommendation response
    recommendations: Dict[str, Union[str, List[str]]] = get_contextual_advice(
        emissions_breakdown
    )

    # 5. Return fully formatted results
    return (
        jsonify(
            {
                "user_message": user_message,
                "parsed_metrics": parsed_metrics,
                "emissions_breakdown": emissions_breakdown,
                "recommendations": recommendations,
                "carbon_log_id": carbon_log.id,
            }
        ),
        200,
    )


@app.route('/api/log', methods=['POST'])
def log_metric() -> Tuple[Response, int]:
    """POST endpoint for saving or overwriting manual carbon metrics in database.

    Returns:
        Tuple[Response, int]: A tuple containing the JSON response and the HTTP status code.

    Raises:
        Exception: If database saving fails.
    """
    logger.info("Received request on manual log endpoint.")
    data: Any = request.get_json()
    if not data:
        return (
            jsonify({"error": "Bad Request", "message": "Missing JSON payload."}),
            400,
        )

    category: Union[str, None] = data.get("category")
    value: Any = data.get("value")
    unit: str = data.get("unit", "kg")

    if not category or value is None:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Both 'category' and 'value' fields are required.",
                }
            ),
            400,
        )

    try:
        metric: Union[CarbonMetric, None] = (
            db.session.query(CarbonMetric).filter_by(category=category).first()
        )
        if metric:
            metric.value = float(value)
            if "unit" in data:
                metric.unit = data["unit"]
        else:
            metric = CarbonMetric(
                category=category, value=float(value), unit=unit
            )
            db.session.add(metric)

        db.session.commit()
        logger.info(
            f"Successfully committed manual CarbonMetric update to database for category: '{category}'."
        )
        return jsonify({"success": True, "metric": metric.to_dict()}), 200
    except ValueError:
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Carbon metric value must be a valid float/number.",
                }
            ),
            400,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Failed to save manual metric to database: {str(e)}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": f"Database error encountered: {str(e)}",
                }
            ),
            500,
        )


@app.errorhandler(404)
def not_found_error(error: Exception) -> Tuple[Response, int]:
    """JSON error handler for page/route not found (HTTP 404).

    Args:
        error (Exception): The exception that triggered the handler.

    Returns:
        Tuple[Response, int]: A tuple containing the JSON response and the HTTP status code.
    """
    logger.info(f"Page or endpoint not found (404): {str(error)}")
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "The requested URL or resource was not found on this server.",
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(error: Exception) -> Tuple[Response, int]:
    """JSON error handler for internal server errors (HTTP 500).

    Args:
        error (Exception): The exception that triggered the handler.

    Returns:
        Tuple[Response, int]: A tuple containing the JSON response and the HTTP status code.
    """
    logger.error(f"Internal Server Error (500): {str(error)}", exc_info=True)
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected server error occurred. Please try again later.",
            }
        ),
        500,
    )


if __name__ == "__main__":
    app.run(debug=True)
