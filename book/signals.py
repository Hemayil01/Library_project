from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Book, BookCopy, BorrowRecord



@receiver(post_save, sender=Book)
def inform_about_book(sender, instance, created, **kwargs):
    if created:
        print('New book is created with title:', instance.title)
    else:
        print('New book is updated with title:', instance.title)


@receiver(pre_save, sender=Book)
def validate_book(sender, instance, **kwargs):
    if Book.objects.filter(isbn=instance.isbn).exclude(id=instance.id).exists():
        raise ValueError('Book with this ISBN already exists')


@receiver(post_save, sender=BookCopy)
def inform_about_book_copy(sender, instance, created, **kwargs):
    if created:
        print('New bookcopy is created for book:', instance.book.title)
    else:
        print('New bookcopy is updated for book:', instance.book.title)


@receiver(pre_save, sender=BookCopy)
def validate_book_copy(sender, instance, **kwargs):
    if instance.status not in dict(BookCopy.Status.choices):
        raise ValueError('Invalid status for bookcopy')


@receiver(post_save, sender=BorrowRecord)
def inform_about_borrow_record(sender, instance, created, **kwargs):
    if created:
        print('New borrowrecord created for book:', instance.book_copy.book.title)
    else:
        print('New borrowrecord updated for book:', instance.book_copy.book.title)


@receiver(pre_save, sender=BorrowRecord)
def validate_borrow_record(sender, instance, **kwargs):
    if instance.return_date and instance.return_date < instance.borrow_date:
        raise ValueError('Return date cannot be before borrow date')
