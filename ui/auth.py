"""
Simple password authentication for CDE Matcher.
"""

import streamlit as st
import os
import hashlib


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_password() -> bool:
    """
    Returns True if password is correct, False otherwise.
    Shows login form if not authenticated.
    """
    # Get password from environment (set this in deployment)
    correct_password_hash = os.getenv('CDE_PASSWORD_HASH')

    # If no password set, skip authentication
    if not correct_password_hash:
        return True

    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        return True

    # Show login form
    st.title("🔐 CDE Matcher - Authentication Required")
    st.markdown("---")

    with st.form("login_form"):
        password = st.text_input("Enter Password:", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if hash_password(password) == correct_password_hash:
                st.session_state.authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")

    st.markdown("---")
    st.info("💡 Contact administrator for access")

    return False


def logout():
    """Clear authentication state."""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    st.rerun()


def generate_password_hash(password: str) -> str:
    """Utility function to generate password hash for deployment."""
    return hash_password(password)


if __name__ == "__main__":
    # Utility to generate password hash
    import sys
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"Password hash for '{password}': {generate_password_hash(password)}")
    else:
        print("Usage: python auth.py <password>")
        print("This will generate a hash to use as CDE_PASSWORD_HASH environment variable")