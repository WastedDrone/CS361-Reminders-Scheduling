# Reminders & Scheduling microservice
# CS361 Team 11
#
# Uses ZeroMQ with JSON messages on port 5556.

import json
import os
from datetime import datetime

import zmq

PORT = 5556
DATA_FILE = os.path.join(os.path.dirname(__file__), "reminders_data.json")


def load_data():
    # no file yet means nothing has been saved
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def error(message):
    return {"status": "error", "message": message}


def valid_date(date):
    # also reject impossible dates like February 30
    if type(date) != str:
        return False
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d") == date
    except ValueError:
        return False


def create_reminder(data, app, title, date):
    if app not in data:
        data[app] = {"next_id": 1, "reminders": []}

    # keep a counter so deleted reminders don't reuse old ids
    reminder_id = data[app]["next_id"]
    reminder = {"id": reminder_id, "title": title, "date": date}

    data[app]["reminders"].append(reminder)
    data[app]["next_id"] += 1
    save_data(data)

    return {
        "status": "success",
        "id": reminder_id,
        "message": "Reminder created",
    }


def view_reminders(data, app):
    if app not in data:
        return {"status": "success", "reminders": []}

    # YYYY-MM-DD dates can be sorted as strings
    reminders = sorted(data[app]["reminders"], key=lambda r: (r["date"], r["id"]))
    return {"status": "success", "reminders": reminders}


def delete_reminder(data, app, reminder_id):
    if app not in data:
        return error(f"No reminder with id {reminder_id}")

    for reminder in data[app]["reminders"]:
        if reminder["id"] == reminder_id:
            data[app]["reminders"].remove(reminder)
            save_data(data)
            return {
                "status": "success",
                "message": f"Reminder {reminder_id} deleted",
            }

    return error(f"No reminder with id {reminder_id}")


def handle_request(message):
    # turn the JSON string into a dictionary
    try:
        request = json.loads(message)
    except (json.JSONDecodeError, TypeError):
        return error("Request is not valid JSON")
    if type(request) != dict:
        return error("Request is not valid JSON")

    action = request.get("action")
    app = request.get("app")
    title = request.get("title")
    date = request.get("date")
    reminder_id = request.get("id")

    # check the parameters before doing anything
    if action not in ["create", "view", "delete"]:
        return error('"action" must be "create", "view", or "delete"')
    if type(app) != str or app.strip() == "":
        return error('"app" is required and must be a string')

    if action == "create":
        if type(title) != str or title.strip() == "":
            return error('"title" is required and must be a string')
        if not valid_date(date):
            return error('"date" must be a valid date in YYYY-MM-DD format')
    elif action == "delete" and (type(reminder_id) != int or reminder_id < 1):
        return error('"id" is required for "delete" and must be a positive number')

    try:
        data = load_data()
        if action == "create":
            return create_reminder(data, app, title, date)
        elif action == "view":
            return view_reminders(data, app)
        else:
            return delete_reminder(data, app, reminder_id)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        # a bad data file should return an error, not be overwritten
        return error(f"Could not access reminders data: {exc}")


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{PORT}")
    print(f"Reminders & Scheduling microservice listening on port {PORT}")

    try:
        while True:
            message = socket.recv_string()
            print("Received request:", message)

            reply = json.dumps(handle_request(message))
            socket.send_string(reply)
            print("Sent reply:      ", reply)
            print()
    except KeyboardInterrupt:
        print("Stopping reminder service")
    finally:
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
