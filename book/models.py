from django.db import models

# author 4 - book 3, book 2  -
# Cascade - author deletion will delete all their books
# PROTECT - author deletion will be prevented if they have books
# SET_NULL - author deletion will set the author field of their books to NULL
# SET_DEFAULT - author deletion will set the author field of their books to a default value
# DO_NOTHING - author deletion will do nothing to their books

from user.models import User

# book 4 - bookcopy 3 , bookcopy 2
# Cascade - book deletion will delete all its copies

# user 3 - borrowrecord 2, borrowrecord 1
# Cascade - user deletion will delete all their borrow records

# bookCopy 3 - borrowrecord 2, borrowrecord 1
# protect - a copy that is borrowed cannot be deleted


class Author(models.Model):
    name = models.CharField(max_length=255)
    biography = models.TextField(null=True, blank=True)
    birth_date = models.DateField()

    def __str__(self):
        return self.name



class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    isbn = models.CharField(max_length=13, unique=True)
    publication_year = models.PositiveIntegerField()
    topics = models.CharField(max_length=255, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    language = models.CharField(max_length=255,choices=
        [
            ('EN', 'English'),
            ('AZ', 'Azerbaijani'),
            ('TR', 'Turkish'),
            ('RU', 'Russian'),
        ],
        default='EN'
    )

    def __str__(self):
        return f'{self.title} ({self.author.name})'

    def available_copies(self):
        borrowed_count = BookCopy.objects.filter(book=self, status=BookCopy.Status.BORROWED).count()
        return self.total_copies - borrowed_count


class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        BORROWED = 'borrowed', 'Borrowed'
        MAINTENANCE = 'maintenance', 'Maintenance'

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    def __str__(self):
        return f'{self.book.title} - {self.get_status_display()}'


class BorrowRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrows')
    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name='borrow_records')
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    late_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.email} - {self.book_copy.book.title}"

    def is_overdue(self):
        from django.utils import timezone
        return self.return_date is None and timezone.now() > self.due_date
