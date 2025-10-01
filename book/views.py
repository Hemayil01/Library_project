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
    search_fields = ['title', 'topics', 'author__name']
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
    

class BorrowRecordAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'PATCH':
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin, IsLibrarianOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated, IsMemberOrAdmin]
        return [perm() for perm in permission_classes]
    
    
    
    def post(self, request):
        book_copy_id = request.data.get('book_copy')
        try:
            book_copy = BookCopy.objects.get(id=book_copy_id)
        except BookCopy.DoesNotExist:
            return Response({'message': 'Book copy not found'}, status=status.HTTP_404_NOT_FOUND)

        if book_copy.status != BookCopy.Status.AVAILABLE:
            return Response({'message': 'Book copy not available'}, status=status.HTTP_400_BAD_REQUEST)

        active_borrows = BorrowRecord.objects.filter(user=request.user, return_date__isnull=True).count()
        if active_borrows >= request.user.borrow_limit:
            return Response({'message': 'Borrow limit reached'}, status=status.HTTP_400_BAD_REQUEST)

        due_date = timezone.now() + timezone.timedelta(days=14)
        borrow_record = BorrowRecord.objects.create(
            user=request.user,
            book_copy=book_copy,
            due_date=due_date
        )
        book_copy.status = BookCopy.Status.BORROWED
        book_copy.save()
        return Response(BorrowRecordModelSerializer(borrow_record).data, status=status.HTTP_201_CREATED)

    def patch(self, request, id=None):
        try:
            borrow_record = BorrowRecord.objects.get(id=id)
        except BorrowRecord.DoesNotExist:
            return Response({'message': 'Borrow record not found'}, status=status.HTTP_404_NOT_FOUND)
        now = timezone.now()
        borrow_record.return_date = now
        borrow_record.save()

        borrow_record.book_copy.status = BookCopy.Status.AVAILABLE
        borrow_record.book_copy.save()

        if now > borrow_record.due_date:
            days_late = (now - borrow_record.due_date).days
            borrow_record.late_fee = decimal.Decimal(days_late) * decimal.Decimal('1.00')
            borrow_record.save()

        return Response(BorrowRecordModelSerializer(borrow_record).data)

    def get(self, request):
        borrows = BorrowRecord.objects.filter(user=request.user)
        return Response(BorrowRecordModelSerializer(borrows, many=True).data)


class MarkFeePaidAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOrAdmin]

    def post(self, request, id):
        try:
            borrow_record = BorrowRecord.objects.get(id=id)
        except BorrowRecord.DoesNotExist:
            return Response({'message': 'Borrow record not found'}, status=status.HTTP_404_NOT_FOUND)

        borrow_record.fee_paid = True
        borrow_record.save()
        return Response({'message': 'Fee marked as paid', 'record': BorrowRecordModelSerializer(borrow_record).data})


class OverdueBorrowRecordsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOrAdmin]

    def get(self, request):
        now = timezone.now()
        overdue_borrows = BorrowRecord.objects.filter(return_date__isnull=True, due_date__lt=now)
        return Response(BorrowRecordModelSerializer(overdue_borrows, many=True).data)