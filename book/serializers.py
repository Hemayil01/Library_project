from rest_framework import serializers
from .models import Book, Author, BookCopy, BorrowRecord


class AuthorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class BookListModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'publication_year', 'language', 'topics']
        read_only_fields = ['id']


class BookModelSerializer(serializers.ModelSerializer):
   class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ["id"]
        extra_kwargs = {
            'publication_year': {'required': False, 'allow_null': True}
        }

class BookCopyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = '__all__'
        read_only_fields = ['id']


class BorrowRecordModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRecord
        fields = '__all__'
        read_only_fields = ['id', 'borrow_date', 'late_fee']
