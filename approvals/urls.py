from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Approval system URLs
router.register(r'approvals', views.EventApprovalViewSet, basename='approval')
router.register(r'approval-pins', views.ParentApprovalPinViewSet, basename='approval-pin')
router.register(r'documents', views.EventDocumentViewSet, basename='document')
router.register(r'document-signatures', views.DocumentSignatureViewSet, basename='document-signature')
router.register(r'letterheads', views.SchoolLetterheadViewSet, basename='letterhead')

app_name = 'approvals'

urlpatterns = [
    path('', include(router.urls)),
]
