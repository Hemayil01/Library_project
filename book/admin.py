from django.contrib import admin
from .models import Author, Book, BookCopy, BorrowRecord


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'birth_date']
    search_fields = ['name',]
    ordering = ['name',]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'publication_year', 'isbn', 'total_copies', 'language']
    list_filter = ['publication_year', 'language']
    search_fields = ['title', 'isbn', 'topics', 'author__name']
    ordering = ['-publication_year',]


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ['book', 'status']
    list_filter = ['status', 'book__title']
    search_fields = ['book__title',]
    ordering = ['book__title',]



@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'book_copy', 'borrow_date', 'due_date', 'return_date', 'late_fee']
    list_filter = ['due_date', 'return_date']
    search_fields = ['user__email', 'book_copy__book__title']
    ordering = ['-borrow_date',]
    readonly_fields = ['borrow_date', 'late_fee']