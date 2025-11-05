# Django Permissions and Authorization Guide

This guide explains the permission system implemented in the **Library_project** and how to use role-based access control effectively.

## Overview

The project includes a complete permission system with four user roles:

* **Admin**: Full access to all operations
* **Librarian**: Can manage books, borrowing, and returns
* **Member**: Can only view books, borrow, and return them
* **Guest**: Can only view public information (books)

---

## Permission System Architecture

### 1. User Roles

The `User` model extends Django's `AbstractUser` with a custom role field:

```python
class Role(models.TextChoices):
    GUEST = 'guest', 'Guest'
    MEMBER = 'member', 'Member'
    LIBRARIAN = 'librarian', 'Librarian'
    ADMIN = 'admin', 'Admin'
```

---

### 2. Custom Permission Classes

Located in `library/permissions.py`, these classes control access to different actions and API endpoints.

#### `CanManageBooks`

* Controls access to book management operations.
* Admins: Full access
* Librarians: Can create, update, delete, and view books
* Members: View only
* Guests: View only (read-only)

#### `CanManageBorrow`

* Controls access to managing or returning books.
* Only librarians and admins can manage or return borrowed books.

#### `CanManageUsers`

* Controls access to user management.
* Only admins can create, update, or delete users.

#### `IsLibrarianOrAdmin`

* General permission for librarian/admin operations.
* Used for book and borrowing-related create, update, and delete actions.

---

### 3. ViewSet Permission Implementation

Each ViewSet implements role-based permissions using the `get_permissions()` method:

```python
def get_permissions(self):
    if self.action in ['list', 'retrieve']:
        # Allow any authenticated user or guest to view
        permission_classes = [permissions.AllowAny]
    elif self.action in ['create', 'update', 'partial_update', 'destroy']:
        # Only librarians and admins can modify
        permission_classes = [permissions.IsAuthenticated, IsLibrarianOrAdmin]
    else:
        permission_classes = self.permission_classes

    return [permission() for permission in permission_classes]
```

---

## API Endpoint Permissions

### Book Endpoints (`/api/books/`)

| Method | Endpoint           | Description    | Admin | Librarian | Member | Guest |
| ------ | ------------------ | -------------- | ----- | --------- | ------ | ----- |
| GET    | `/api/books/`      | List books     | ✓     | ✓         | ✓      | ✓     |
| GET    | `/api/books/{id}/` | Retrieve book  | ✓     | ✓         | ✓      | ✓     |
| POST   | `/api/books/`      | Create book    | ✓     | ✓         | ✗      | ✗     |
| PUT    | `/api/books/{id}/` | Update book    | ✓     | ✓         | ✗      | ✗     |
| PATCH  | `/api/books/{id}/` | Partial update | ✓     | ✓         | ✗      | ✗     |
| DELETE | `/api/books/{id}/` | Delete book    | ✓     | ✓         | ✗      | ✗     |

### Borrow Endpoints (`/api/borrow/`)

| Method | Endpoint                    | Description         | Admin | Librarian | Member       | Guest |
| ------ | --------------------------- | ------------------- | ----- | --------- | ------------ | ----- |
| GET    | `/api/borrow/`              | List borrow records | ✓     | ✓         | ✓            | ✗     |
| POST   | `/api/borrow/`              | Borrow book         | ✓     | ✓         | ✓            | ✗     |
| POST   | `/api/return/{id}/`         | Return book         | ✓     | ✓         | ✓            | ✗     |
| PUT    | `/api/borrow/{id}/manage/`  | Manage borrow      | ✓     | ✓         | ✗            | ✗     |

### User Endpoints (`/api/users/`)

| Method | Endpoint           | Description   | Admin | Librarian | Member   | Guest |
| ------ | ------------------ | ------------- | ----- | --------- | -------- | ----- |
| GET    | `/api/users/`      | List users    | ✓     | ✗         | ✗        | ✗     |
| GET    | `/api/users/{id}/` | Retrieve user | ✓     | ✓         | ✓        | ✗     |
| POST   | `/api/users/`      | Create user   | ✓     | ✗         | ✗        | ✗     |
| PUT    | `/api/users/{id}/` | Update user   | ✓     | ✗         | ✓        | ✗     |
| DELETE | `/api/users/{id}/` | Delete user   | ✓     | ✗         | ✗        | ✗     |

---

## Utility Functions

Located in `library/utils.py`, these helper functions assist in permission checks.

### Role Checking Functions

* `has_role(user, role)`: Check if a user has a specific role.
* `has_any_role(user, roles)`: Check if a user has any of the specified roles.
* `is_admin(user)`: Check if user is an admin.
* `is_librarian(user)`: Check if user is a librarian.
* `is_member(user)`: Check if user is a member.
* `is_guest(user)`: Check if user is a guest.
* `is_librarian_or_admin(user)`: Check if user is either librarian or admin.

### Permission Checking Functions

* `can_manage_books(user)`: Verify if user can manage books.
* `can_manage_borrow(user)`: Verify if user can manage borrow requests.
* `can_manage_users(user)`: Verify if user can manage user accounts.

### Helper Function

* `get_user_permissions(user)`: Return all user permissions as a dictionary.

---

## Usage Examples

### 1. Using Permission Classes in Views

```python
from rest_framework import viewsets, permissions
from .permissions import CanManageBooks, IsLibrarianOrAdmin

class BookViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanManageBooks]

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsLibrarianOrAdmin]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
```

### 2. Using Utility Functions

```python
from library.utils import can_manage_books, get_user_permissions

def some_view(request):
    if can_manage_books(request.user):
        # User can manage books
        pass

    permissions = get_user_permissions(request.user)
    if permissions['can_manage_borrow']:
        # User can manage borrow requests
        pass
```

### 3. Custom Action Permissions

```python
@action(detail=True, methods=['post'], url_path='approve', permission_classes=[CanManageBorrow])
def manage_borrow(self, request, pk=None):
    # Only librarians or admins can manage borrows
    pass
```

---

## Testing Permissions

Run the test script to verify permissions work correctly:

```bash
python test_permissions.py
```

This will:

1. Create test users with different roles
2. Test utility functions
3. Test permission classes
4. Simulate API endpoint access control

---

## Best Practices

1. **Always check authentication first**: Validate users before permission checks.
2. **Use specific permissions**: Create fine-grained permission classes.
3. **Test thoroughly**: Always verify permission behavior for each role.
4. **Document permissions**: Keep this file updated.
5. **Use utility functions**: Ensure consistency in role and permission logic.

---

## Security Considerations

1. **Never rely on client-side checks**: Always enforce permission logic server-side.
2. **Use HTTPS**: Ensure encrypted communication.
3. **Review regularly**: Audit permission logic periodically.
4. **Apply least privilege**: Users should only get necessary permissions.
5. **Log permission checks**: Maintain activity logs for audits.

---

## Extending the Permission System

To add a new permission:

1. Create a new permission class in `library/permissions.py`
2. Add utility functions in `library/utils.py`
3. Update ViewSets to use the new permission
4. Update this documentation
5. Write unit tests
Example:

```python
class CanManageInventory(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'librarian']
```
