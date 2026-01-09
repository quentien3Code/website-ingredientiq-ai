"""
Helper functions for foodinfo app.
Extracted from views.py during cleanup - mobile app terminated.
"""
from .models import AccountDeletionRequest


def safe_delete_user(user):
    """
    Safely delete a user account, handling all foreign key constraints
    """
    try:
        # Delete any existing deletion request first to avoid foreign key constraints
        try:
            deletion_request = AccountDeletionRequest.objects.get(user=user)
            deletion_request.delete()
        except AccountDeletionRequest.DoesNotExist:
            pass
        
        # Delete the user (this will cascade delete all related objects)
        user.delete()
        return True, "User deleted successfully"
    except Exception as e:
        return False, f"Error deleting user: {str(e)}"
