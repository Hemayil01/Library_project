from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


def has_role(user, role):
    if not user or not user.is_authenticated:
        return False
    return user.role == role


def has_any_role(user, roles):
    if not user or not user.is_authenticated:
        return False
    return user.role in roles


def is_admin(user):
    return has_role(user, 'admin')


def is_librarian(user):
    return has_role(user, 'librarian')


def is_member(user):
    return has_role(user, 'member')


def is_librarian_or_admin(user):
    return has_any_role(user, ['librarian', 'admin'])


def can_manage_books(user):
    if not user or not user.is_authenticated:
        return False

    if user.role == 'admin':
        return True
    elif user.role == 'librarian':
        return True
    elif user.role == 'member':
        return False

    return False


def can_manage_book_copies(user):
    if not user or not user.is_authenticated:
        return False

    if user.role == 'admin':
        return True
    elif user.role == 'librarian':
        return True
    elif user.role == 'member':
        return False

    return 

def can_manage_borrow(user):
    if not user or not user.is_authenticated:
        return False

    if user.role == 'admin':
        return True
    elif user.role == 'librarian':
        return True

    return False


def get_user_permissions(user):
    if not user or not user.is_authenticated:
        return {
            'can_view_books': False,
            'can_create_books': False,
            'can_update_books': False,
            'can_delete_books': False,
            'can_manage_copies': False,
            'can_manage_borrow': False,
        }

    return {
        'can_view_books': True,
        'can_create_books': can_manage_books(user),
        'can_update_books': can_manage_books(user),
        'can_delete_books': can_manage_books(user),
        'can_manage_copies': can_manage_book_copies(user),
        'can_manage_borrow': can_manage_borrow(user),
    }
