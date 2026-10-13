class AuthError(Exception):
    """The base class error for the auto modele""" 


class EmailAlreadyRegistered(AuthError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email {email} is already registered")
class WeakPassword(AuthError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Password is too weak: {reason}")
    