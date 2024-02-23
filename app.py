from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, subprocess, shutil, time, shlex

# Initialize Flask application
app = Flask(__name__)
# Set a secret key for session management
app.secret_key = 'SuperSecretPassword'
# Configure SQLAlchemy with SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///venvs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Directory to store virtual environments
VENV_DIR = "venvs"
# Ensure the directory exists
os.makedirs(VENV_DIR, exist_ok=True)

# Define a database model for logging virtual environment operations
class VenvLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venv_name = db.Column(db.String(80), nullable=True, index=True)  # Virtual environment name
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)  # Timestamp of the log entry
    log_message = db.Column(db.String(255), nullable=False)  # Log message
    log_type = db.Column(db.String(50), nullable=False)  # Type of log (e.g., create, delete)
    command_output = db.Column(db.Text, nullable=True)  # Output of the command executed

    def __repr__(self):
        return f'<VenvLog {self.venv_name}: {self.log_message}>'

# Route to display the main page
@app.route('/')
def index():
    # List all virtual environments and logs
    venvs = os.listdir(VENV_DIR)
    logs = VenvLog.query.order_by(VenvLog.timestamp.desc()).all()
    return render_template('index.html', venvs=venvs, logs=logs)

# Route to create a new virtual environment
@app.route('/create', methods=['POST'])
def create_venv():
    venv_name = request.form.get('venv_name')
    if venv_name:
        # Create the virtual environment
        result = subprocess.run(["python", "-m", "venv", os.path.join(VENV_DIR, venv_name)], capture_output=True, text=True)
        # Log the operation
        log_message = "Virtual environment created successfully." if result.returncode == 0 else "Error creating virtual environment."
        new_log = VenvLog(venv_name=venv_name, log_message=log_message, log_type="create", command_output=result.stdout or result.stderr)
        db.session.add(new_log)
        db.session.commit()
        # Provide user feedback
        if result.returncode == 0:
            flash(log_message, "success")
        else:
            flash(log_message, "danger")
    return redirect(url_for('index'))

# Route to delete a virtual environment
@app.route('/delete/<venv_name>')
def delete_venv(venv_name):
    venv_path = os.path.join(VENV_DIR, venv_name)
    if os.path.exists(venv_path):
        try:
            # Delete the virtual environment directory
            shutil.rmtree(venv_path)
            log_message = f"Virtual environment '{venv_name}' deleted successfully."
            flash(log_message, "success")
            command_output = ""
        except Exception as e:
            log_message = f"Error deleting virtual environment '{venv_name}': {e}"
            flash(log_message, "danger")
            command_output = str(e)
        # Log the operation
        new_log = VenvLog(venv_name=venv_name, log_message=log_message, log_type="delete", command_output=command_output)
        db.session.add(new_log)
        db.session.commit()
    else:
        flash(f"Virtual environment '{venv_name}' does not exist.", "warning")
    return redirect(url_for('index'))

# Route to execute a command within a virtual environment
@app.route('/run/<venv_name>', methods=['POST'])
def run_venv(venv_name):
    data = request.get_json()
    command = data.get('command') if data else None
    if not command:
        return jsonify({"success": False, "output": "No command provided"}), 400

    # Prevent directory traversal
    venv_name = os.path.basename(venv_name)
    venv_path = os.path.join(VENV_DIR, venv_name)
    
    # Check if the virtual environment exists
    if not os.path.exists(venv_path):
        return jsonify({"success": False, "output": "Virtual environment does not exist"}), 404

    # Determine the path to the Python executable in the virtual environment
    python_executable = os.path.join(venv_path, 'Scripts' if os.name == 'nt' else 'bin', 'python')
    
    # Safely parse the command string
    try:
        command_parts = shlex.split(command)
    except ValueError as e:
        return jsonify({"success": False, "output": str(e)}), 400

    # Execute the command
    command_to_run = [python_executable] + command_parts

    try:
        result = subprocess.run(command_to_run, capture_output=True, text=True, check=True)
        return jsonify({"success": True, "output": result.stdout}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "output": e.stderr}), 400
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"success": False, "output": f"An error occurred: {str(e)}"}), 500
    
# Route to fetch command history
@app.route('/command-history')
def command_history():
    # Fetch the last 10 command logs
    command_logs = VenvLog.query.order_by(VenvLog.timestamp.desc()).limit(10).all()
    # Format logs for JSON response
    command_history = [{'venv_name': log.venv_name, 'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'log_message': log.log_message, 'log_type': log.log_type, 'command_output': log.command_output} for log in command_logs]
    return jsonify(command_history)

# Route to open a virtual environment folder
@app.route('/open/<venv_name>')
def open_venv_folder(venv_name):
    venv_path = os.path.join(VENV_DIR, venv_name)
    if os.path.exists(venv_path):
        try:
            # Open the virtual environment folder
            os.startfile(venv_path)
            flash(f"Opened virtual environment folder '{venv_name}'.", "success")
        except Exception as e:
            flash(f"Error opening virtual environment folder '{venv_name}': {e}", "danger")
    else:
        flash(f"Virtual environment '{venv_name}' does not exist.", "warning")
    return redirect(url_for('index'))

# Function to create database tables
def create_tables():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)