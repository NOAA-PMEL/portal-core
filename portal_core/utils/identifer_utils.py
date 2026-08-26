import hashlib
import time

def create_submission_id(user_id):
    """Creates a submission id from the time stamp, user id and random word"""
    # Ingredients: Timestamp, User ID, and a random word
    timestamp = str(time.time_ns())
    salt = "data_submission_salt"
    raw_string = f"{timestamp}-{user_id}-{salt}"

    return hashlib.sha256(raw_string.encode()).hexdigest()[:16]