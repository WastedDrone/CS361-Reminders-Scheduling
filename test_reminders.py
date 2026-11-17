# Test program for the Reminders & Scheduling microservice
# CS361 Team 11
#
# This program does NOT import or call reminder_service.py directly.
# It only talks to the microservice through ZeroMQ, sending JSON
# requests and receiving JSON replies on port 5556.
#
# How to run:
#   Terminal 1:  python3 reminder_service.py
#   Terminal 2:  python3 test_reminders.py

import json
import zmq

APP = "test_program"


def send_request(socket, request):
    """Sends one JSON request to the microservice and returns its reply."""
    print("REQUEST SENT:    ", json.dumps(request))
    socket.send_string(json.dumps(request))      # request data

    reply = json.loads(socket.recv_string())     # receive data
    print("REPLY RECEIVED:  ", json.dumps(reply))
    print()
    return reply


def main():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5556")
    print("Connected to the Reminders microservice on port 5556\n")

    # 1. Create a reminder
    print("--- Test 1: Create a reminder ---")
    reply = send_request(socket, {
        "action": "create",
        "app": APP,
        "title": "Pay phone bill",
        "date": "2026-11-20",
    })
    new_id = reply["id"]

    # 2. Create a second reminder
    print("--- Test 2: Create another reminder ---")
    send_request(socket, {
        "action": "create",
        "app": APP,
        "title": "CS361 assignment due",
        "date": "2026-11-18",
    })

    # 3. View all reminders (sorted by date)
    print("--- Test 3: View reminders ---")
    reply = send_request(socket, {"action": "view", "app": APP})
    for reminder in reply["reminders"]:
        print(f"  #{reminder['id']}  {reminder['date']}  {reminder['title']}")
    print()

    # 4. Delete the first reminder
    print(f"--- Test 4: Delete reminder {new_id} ---")
    send_request(socket, {"action": "delete", "app": APP, "id": new_id})

    # 5. View again to show it was deleted
    print("--- Test 5: View reminders after delete ---")
    reply = send_request(socket, {"action": "view", "app": APP})
    for reminder in reply["reminders"]:
        print(f"  #{reminder['id']}  {reminder['date']}  {reminder['title']}")
    print()

    # 6. Bad request: invalid date returns an error
    print("--- Test 6: Invalid date (error reply) ---")
    send_request(socket, {
        "action": "create",
        "app": APP,
        "title": "Bad date test",
        "date": "2026-02-30",
    })

    socket.close()
    context.term()
    print("All tests finished.")


if __name__ == "__main__":
    main()
