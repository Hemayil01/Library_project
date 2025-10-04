from django_filters import rest_framework as filters
from .models import Book, BookCopy, BorrowRecord


class BookFilter(filters.FilterSet):
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    author = filters.CharFilter(field_name='author', lookup_expr='icontains')
    topics = filters.CharFilter(field_name='topics', lookup_expr='icontains')
    publication_year_min = filters.NumberFilter(field_name='publication_year', lookup_expr='gte')
    publication_year_max = filters.NumberFilter(field_name='publication_year', lookup_expr='lte')
    language = filters.ChoiceFilter(field_name='language',choices=Book._meta.get_field('language').choices)
    available_only = filters.BooleanFilter(method='filter_available', label='Only available books')

    class Meta:
        model = Book
        fields = ['title', 'author', 'topics', 'publication_year', 'language']

    def filter_available(self, queryset, name, value):
        if value:
            return queryset.filter(copies__status=BookCopy.Status.AVAILABLE).distinct()
        return queryset


class BookCopyFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    book_id = filters.NumberFilter(field_name='book__id')

    class Meta:
        model = BookCopy
        fields = ['status', 'book_id']


class BorrowRecordFilter(filters.FilterSet):
    user_id = filters.NumberFilter(field_name='user__id')
    book_title = filters.CharFilter(field_name='book_copy__book__title', lookup_expr='icontains')
    overdue = filters.BooleanFilter(method='filter_overdue')

    class Meta:
        model = BorrowRecord
        fields = ['user_id', 'book_title']

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(return_date__isnull=True, due_date__lt=timezone.now())
        return queryset
