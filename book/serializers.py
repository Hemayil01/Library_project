from rest_framework import serializers
from datetime import datetime
from .models import Book, BookCopy, BorrowRecord


class BookListModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'publication_year', 'language', 'topics']
        read_only_fields = ['id']
        

class BookModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['id']
        extra_kwargs = {
            'publication_year': {'required': False, 'allow_null': True}
        }

    def validate_publication_year(self, value):
        current_year = datetime.now().year
        if value < 1500 or value > current_year:
            raise serializers.ValidationError('Publication year must be between 1500 and current_year')
        return value
    

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

    def validate_book_copy(self, value):
        if value.status != BookCopy.Status.AVAILABLE:
            raise serializers.ValidationError('Book copy not available')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        active_borrows = BorrowRecord.objects.filter(user=user, return_date__isnull=True).count()
        if active_borrows >= user.borrow_limit:
            raise serializers.ValidationError('Borrow limit reached')
        return attrs