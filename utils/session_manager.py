from config import PROJECT_DIR, SESSION_TTL
import shutil
import time
import uuid
import json
import os


class SessionManager:

    @staticmethod
    def create_session():
        session_id = str(uuid.uuid4())[:8]
        session_path = os.path.join(PROJECT_DIR, session_id)
        os.makedirs(session_path, exist_ok=True)
        for folder in ["project", "cache"]:
            os.makedirs(os.path.join(session_path, folder), exist_ok=True)
        metadata = {
            "session_id": session_id,
            "created_at": time.time(),
            "expires_at": time.time() + SESSION_TTL,
            "ttl": SESSION_TTL,
            "status": "ACTIVE"
        }
        metadata_file = os.path.join(session_path, "metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)
        return session_id

    @staticmethod
    def get_session_path(session_id):
        return os.path.join(PROJECT_DIR, session_id)

    @staticmethod
    def get_project_path(session_id):
        return os.path.join(
            SessionManager.get_session_path(session_id),
            "project"
        )

    @staticmethod
    def load_metadata(session_id):
        metadata_file = os.path.join(
            SessionManager.get_session_path(session_id),
            "metadata.json"
        )
        if not os.path.exists(metadata_file):
            return None
        with open(metadata_file, "r") as f:
            return json.load(f)

    @staticmethod
    def is_session_expired(session_id):
        metadata = SessionManager.load_metadata(session_id)
        if metadata is None:
            return True
        return (time.time() > metadata["expires_at"])

    @staticmethod
    def delete_session(session_id):
        session_path = SessionManager.get_session_path(session_id)
        if os.path.exists(session_path):
            shutil.rmtree(session_path)

    @staticmethod
    def cleanup_expired_sessions():
        if not os.path.exists(PROJECT_DIR):
            return
        for session_id in os.listdir(PROJECT_DIR):
            try:
                if SessionManager.is_session_expired(session_id):
                    SessionManager.delete_session(session_id)
            except Exception as e:
                pass


from functools import wraps
import streamlit as st

class SessionExpiredError(Exception):
    pass


def session_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        # Try to get session_id from kwargs
        session_id = st.session_state.get("session_id")

        if not session_id:
            raise SessionExpiredError(
                "Session expired. Please upload the project again."
            )

        if SessionManager.is_session_expired(session_id):
            raise SessionExpiredError(
                "Session expired. Please upload the project again."
            )


        return func(*args, **kwargs)
    return wrapper
   