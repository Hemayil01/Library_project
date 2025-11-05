from rest_framework.response import Response
from .models import Book, BookCopy, BorrowRecord
from .serializers import BookModelSerializer, BookListModelSerializer, BookCopyModelSerializer, BorrowRecordModelSerializer
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action
import decimal
from django.utils import timezone
from rest_framework import permissions, status
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from .permissions import (
    IsLibrarianOrAdmin,
    IsMemberOrAdmin,
    IsOwnerOrAdmin,
    IsAdminOrReadOnly,
    CanManageBooks,
    CanManageBookCopies,
    CanManageBorrow
    )
from .paginators import CustomPageNumberPagination
from .filters import BookFilter


class HealthCheckAPIView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})
    

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookModelSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageBooks]
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['title', 'topics', 'author']
    ordering_fields = ['publication_year', 'title', 'total_copies']
    ordering = ['-publication_year']
    filterset_class = BookFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListModelSerializer
        return BookModelSerializer
    
    def get_queryset(self):
        return self.queryset


    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'available_copies']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
        return [perm() for perm in permission_classes]

    @action(detail=True, methods=['get'], url_path='available_copies',
            permission_classes=[permissions.AllowAny])
    def available_copies(self, request, pk=None):
        book = self.get_object()
        return Response({'available_copies': book.available_copies()})

class BookCopyViewSet(viewsets.ModelViewSet):
    queryset = BookCopy.objects.all()
    serializer_class = BookCopyModelSerializer
    filter_backends = [drf_filters.OrderingFilter]
    ordering_fields = ['status', 'book__title']
    ordering = ['book__title']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, CanManageBookCopies]
        return [perm() for perm in permission_classes]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        status_value = serializer.validated_data.get('status')
        allowed_statuses = [BookCopy.Status.AVAILABLE, BookCopy.Status.BORROWED]

        if status_value not in allowed_statuses:
            return Response({'message': 'Invalid book copy status.'}, status=status.HTTP_400_BAD_REQUEST)

        book_copy = serializer.save()
        return Response(BookCopyModelSerializer(book_copy).data, status=status.HTTP_201_CREATED)
    

class BorrowRecordAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'PATCH':
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin, CanManageBorrow]
        else:
            permission_classes = [permissions.IsAuthenticated, IsMemberOrAdmin]
        return [perm() for perm in permission_classes]
    
    def post(self, request, id=None):
        if id is not None:
            return self.return_book(request, id)
        return self.borrow_book(request)

    def borrow_book(self, request):
        serializer = BorrowRecordModelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book_copy = serializer.validated_data.get('book_copy')

        borrow_record = BorrowRecord.objects.create(
            user=request.user,
            book_copy=book_copy
        )
        
        book_copy.status = BookCopy.Status.BORROWED
        book_copy.save()
        return Response({'message': 'Book borrowed successfully', 'record': BorrowRecordModelSerializer(borrow_record).data}, status=status.HTTP_201_CREATED)

    def return_book(self, request, id=None):
        try:
            borrow_record = BorrowRecord.objects.get(id=id)
        except BorrowRecord.DoesNotExist:
            return Response({'message': 'Borrow record not found'}, status=status.HTTP_404_NOT_FOUND)
        now = timezone.now()
        
        if request.user.role in ['librarian', 'admin']:
            pass
        elif borrow_record.user != request.user:
            return Response({'message': 'You can only return your own books'}, status=status.HTTP_403_FORBIDDEN)

        
        if borrow_record.due_date and now > borrow_record.due_date:
            days_late = max(0, (now - borrow_record.due_date).days)
            borrow_record.late_fee = decimal.Decimal(days_late) * decimal.Decimal('1.00')
        else:
            borrow_record.late_fee = decimal.Decimal('0.00')
            
        borrow_record.return_date = now
        borrow_record.book_copy.status = BookCopy.Status.AVAILABLE
        borrow_record.book_copy.save()
        borrow_record.save()
        return Response({'message': 'Book returned successfully', 'record': BorrowRecordModelSerializer(borrow_record).data}, status=status.HTTP_200_OK)
    

    def get(self, request):
        if request.user.role in ['librarian', 'admin']:
            borrows = BorrowRecord.objects.all()
        else:
            borrows = BorrowRecord.objects.filter(user=request.user)
        return Response(BorrowRecordModelSerializer(borrows, many=True).data)
    
    
class BorrowListAPIView(APIView):
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOrAdmin]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        queryset = super().get_queryset()
        if status_filter == 'overdue':
            now = timezone.now()
            queryset = queryset.filter(return_date__isnull=True, due_date__lt=now)
        return queryset
    
    def get(self, request):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MarkFeePaidAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOrAdmin]

    def post(self, request, id):
        try:
            borrow_record = BorrowRecord.objects.get(id=id)
        except BorrowRecord.DoesNotExist:
            return Response({'message': 'Borrow record not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if borrow_record.late_fee <= 0:
            return Response({'message': 'No late fee to mark as paid'},status=status.HTTP_400_BAD_REQUEST)
        
        serializer = BorrowRecordModelSerializer(borrow_record,data={'fee_paid': True},partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Fee marked as paid', 'record': serializer.data})