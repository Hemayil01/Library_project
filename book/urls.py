from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

"""
Book endpoints:
 - book list: lists all books
 - book detail: retrieves a specific book by ID
"""

router = DefaultRouter()
router.register('books', views.BookViewSet, basename='books')
router.register('authors', views.AuthorViewSet, basename='authors')
router.register('copies', views.BookCopyViewSet, basename='copies')

urlpatterns = [
    path('health_check/', views.HealthCheckAPIView.as_view(), name='health-check'),
    path('borrow/', views.BorrowRecordAPIView.as_view(), name='borrow-book'),
    path('return/<int:id>/', views.BorrowRecordAPIView.as_view(), name='return-book'),
    path('my-borrows/', views.BorrowRecordAPIView.as_view(), name='my-borrows'),
    path('overdue-borrows/', views.OverdueBorrowRecordsAPIView.as_view(), name='overdue-borrows'),
]

urlpatterns += router.urls

"""
books/ - list
books/ - create
books/id/ - retrieve
books/id/ - update|partial_update
books/id/ - destroy
books/id/available_copies/ - available copies
authors/ - list|create
authors/id/ - retrieve|update|delete
copies/ - list|create|update|delete
borrow/ - borrow a book copy {'book_copy': 1}
return/id/ - return a book copy
my-borrows/ - list user's borrow records
overdue-borrows/ - list all overdue borrows (librarian/admin)
"""
