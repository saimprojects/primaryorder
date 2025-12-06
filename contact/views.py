# contact/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q
from .models import ContactMessage
from .serializers import ContactMessageSerializer, AdminContactMessageSerializer

class ContactMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]  # Allow anyone to submit contact form
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return ContactMessage.objects.all()
        
        if user.is_authenticated:
            return ContactMessage.objects.filter(
                Q(user=user) | Q(email=user.email)
            )
        
        # For non-authenticated users, they can only see their own messages by email
        email = self.request.query_params.get('email', None)
        if email:
            return ContactMessage.objects.filter(email=email)
        
        return ContactMessage.objects.none()
    
    def get_serializer_class(self):
        if self.request.user.is_staff:
            return AdminContactMessageSerializer
        return ContactMessageSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def respond(self, request, pk=None):
        message = self.get_object()
        response_text = request.data.get('response', '').strip()
        
        if not response_text:
            return Response(
                {'error': 'Response text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.admin_response = response_text
        message.status = 'in_progress'
        message.responded_by = request.user
        message.save()
        
        return Response({'status': 'Response added successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_resolved(self, request, pk=None):
        message = self.get_object()
        message.mark_as_resolved(request.user)
        return Response({'status': 'Message marked as resolved'})
    
    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        messages = ContactMessage.objects.filter(
            Q(user=request.user) | Q(email=request.user.email)
        )
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class ContactStatsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    
    def list(self, request):
        stats = {
            'total_messages': ContactMessage.objects.count(),
            'new_messages': ContactMessage.objects.filter(status='new').count(),
            'in_progress': ContactMessage.objects.filter(status='in_progress').count(),
            'resolved': ContactMessage.objects.filter(status='resolved').count(),
            'by_priority': {
                'low': ContactMessage.objects.filter(priority='low').count(),
                'medium': ContactMessage.objects.filter(priority='medium').count(),
                'high': ContactMessage.objects.filter(priority='high').count(),
            }
        }
        return Response(stats)