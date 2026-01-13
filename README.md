**Vibe Check Polling API**
A REST API for a real-time polling system built with Python and FastAPI. This project implements a polling engine where users can create polls, view results, and cast votes, with strict logic to prevent double-voting.


**Features**
Create Polls: Define a question and multiple options.
Real-time Results: View current vote counts instantly.
Data Integrity: Composite Unique Constraints in the database prevent users from voting twice on the same poll.


**Tech Stack**
Language: Python 3.12+
Framework: FastAPI
Database: SQLite (SQLAlchemy ORM)
Validation: Pydantic


**How to Run**
Clone the repository: git clone https://github.com/FurquanEats/Vibe-API-Assignment cd vibe-check-api

Set up the environment: python -m venv venv .\venv\Scripts\activate

Install dependencies: pip install -r requirements.txt

Start the server: uvicorn main:app --reload

Test the API: Open http://127.0.0.1:8000/docs in your browser to use the Swagger UI.


**Testing Guide (Quick Start)**
You can test the API using the Swagger UI at /docs or via curl/Postman.

**1. Create a Poll**
Endpoint: POST /polls

**JSON Body:**

    {
      "question": "What is your favorite backend language?",
      "options": ["Python", "Go", "Node.js"]
    }

**2. Cast a Vote**
Endpoint: POST /polls/{id}/vote

**JSON Body:**

    {
      "user_id": "test_user_1",
      "option_id": 1
    }
    
**Note:** If you try to send this exact request twice, the second attempt will fail with a 400 error (Duplicate Vote Prevention).

**3. View Results**
Endpoint: GET /polls/{id}

**Response:**

    {
      "id": 1,
      "question": "What is your favorite backend language?",
      "options": [
        { "option_id": 1, "text": "Python", "votes": 1 },
        { "option_id": 2, "text": "Go", "votes": 0 },
        { "option_id": 3, "text": "Node.js", "votes": 0 }
      ]
    }



**Design Logic: The "One Vote" Rule**
To ensure efficiency and correctness, the "one vote per user" rule is enforced at the Database Schema Level, not just in the application code.
A Unique Constraint is applied to the votes table on the pair (user_id, poll_id).
If a user tries to vote again, the database engine creates an integrity error.
The API catches this error and returns a clean 400 Bad Request response.
This approach is faster (O(1)) and safer than querying the database before every insertion to check for duplicates.
