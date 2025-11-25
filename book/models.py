from django.db import models
from datetime import timedelta
from django.utils import timezone

from user.models import User


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
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
        return f'{self.title} ({self.author})'

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
    
    def is_available(self):
        return self.status == self.Status.AVAILABLE


class BorrowRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrows')
    book_copy = models.ForeignKey(BookCopy, on_delete=models.PROTECT, related_name='borrow_records')
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fee_paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.email} - {self.book_copy.book.title}'

    def is_overdue(self):
        return self.return_date is None and timezone.now() > self.due_date
    
    def save(self, *args, **kwargs):
        if not self.borrow_date:
            self.borrow_date = timezone.now()
        if not self.due_date or self.due_date <= self.borrow_date:
            self.due_date = self.borrow_date + timedelta(days=14)
        super().save(*args, **kwargs)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(due_date__gt=models.F('borrow_date')),
                name='check_due_date_after_borrow_date'
            )
        ]
