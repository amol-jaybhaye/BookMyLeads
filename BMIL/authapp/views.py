from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Lead, Review, Wishlist, Cart, Address
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import LeadSerializer, ReviewSerializer
from .serializers import WishlistSerializer, CartSerializer, AddressSerializer
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import requests

#SignUp
class SignUpView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

#SignIn
class SigninView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

# Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)

#Get profile
class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
#Leads Section
class LeadListCreateView(generics.GenericAPIView):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        leads = Lead.objects.all()
        serializer = self.get_serializer(leads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeadRetrieveUpdateDeleteView(generics.GenericAPIView):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, lead_id):
        try:
            return Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return None

    def get(self, request, lead_id):
        lead = self.get_object(lead_id)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(lead)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, lead_id):
        lead = self.get_object(lead_id)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(lead, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, lead_id):
        lead = self.get_object(lead_id)
        if not lead:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)
        
        lead.delete()
        return Response({"message": "Lead deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class ReviewListCreateView(generics.GenericAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, lead_id):
        """Get all reviews for a specific lead"""
        reviews = Review.objects.filter(lead_id=lead_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, lead_id):
        """Create a new review for a specific lead"""
        try:
            lead = Lead.objects.get(id=lead_id)  # 🔹 Ensure lead exists
        except Lead.DoesNotExist:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()  # 🔹 Copy request data
        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            serializer.save(lead=lead, user=request.user)  # 🔹 Explicitly pass lead & user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewRetrieveUpdateDeleteView(generics.GenericAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, review_id):
        try:
            return Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return None

    def get(self, request, review_id):
        """Get a single review"""
        review = self.get_object(review_id)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, review_id):
        """Update a review (only by the review creator)"""
        review = self.get_object(review_id)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user != review.user:
            return Response({"error": "You can only update your own review"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, review_id):
        """Delete a review (only by the review creator)"""
        review = self.get_object(review_id)
        if not review:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user != review.user:
            return Response({"error": "You can only delete your own review"}, status=status.HTTP_403_FORBIDDEN)

        review.delete()
        return Response({"message": "Review deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class WishlistView(generics.GenericAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all wishlist items for the logged-in user"""
        wishlists = Wishlist.objects.filter(user=request.user)
        serializer = self.get_serializer(wishlists, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, lead_id):
        """Add a lead to the wishlist"""
        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, lead=lead)

        if not created:
            return Response({"message": "Lead already in wishlist"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(WishlistSerializer(wishlist_item).data, status=status.HTTP_201_CREATED)

    def delete(self, request, lead_id):
        """Remove a lead from the wishlist"""
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, lead_id=lead_id)
            wishlist_item.delete()
            return Response({"message": "Removed from wishlist"}, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({"error": "Lead not in wishlist"}, status=status.HTTP_404_NOT_FOUND)    
        
class CartView(generics.GenericAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all cart items for the logged-in user"""
        cart_items = Cart.objects.filter(user=request.user)
        serializer = self.get_serializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, lead_id):
        """Add a lead to the cart or update quantity"""
        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return Response({"error": "Lead not found"}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get("quantity", 1)  # Default quantity = 1

        cart_item, created = Cart.objects.get_or_create(user=request.user, lead=lead, defaults={"quantity": quantity})

        if not created:
            cart_item.quantity += int(quantity)  # Increase quantity if already in cart
            cart_item.save()

        return Response(CartSerializer(cart_item).data, status=status.HTTP_201_CREATED)

    def delete(self, request, lead_id):
        """Remove a lead from the cart"""
        try:
            cart_item = Cart.objects.get(user=request.user, lead_id=lead_id)
            cart_item.delete()
            return Response({"message": "Removed from cart"}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"error": "Lead not in cart"}, status=status.HTTP_404_NOT_FOUND)
        
def download_lead_pdf(request, lead_id):
    """Generate and download a professional-looking PDF for a specific lead"""
    try:
        lead = Lead.objects.get(id=lead_id)
    except Lead.DoesNotExist:
        return HttpResponse("Lead not found", status=404)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="lead_{lead_id}.pdf"'

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # Page size

    # 🔹 **Set Header Title**
    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColor(colors.darkblue)
    pdf.drawString(200, height - 50, "Lead Details Report")
    pdf.setStrokeColor(colors.black)
    pdf.line(50, height - 55, 550, height - 55)  # Add line below title

    # 🔹 **Lead Details in a Box**
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.black)
    pdf.rect(50, height - 280, 500, 200, stroke=True, fill=False)  # Box for details

    details = [
        ["Name:", lead.name],
        ["Location:", lead.location],
        ["Property Type:", lead.property_type],
        ["Property Status:", lead.property_status],
        ["Service Required On:", lead.service_required_on],
        ["Budget:", f"Rs {lead.budget}"],
        ["Requirement:", lead.requirement],
        ["Tags:", lead.tags if lead.tags else "N/A"],
        ["Price:", f"Rs {lead.price} (Discounted: Rs {lead.discount_price})"],
    ]

    table = Table(details, colWidths=[150, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))

    table.wrapOn(pdf, 50, height - 280)
    table.drawOn(pdf, 55, height - 270)

    # 🔹 **Include Image if Available**
    if lead.image_url:
        try:
            img_response = requests.get(lead.image_url, stream=True)
            if img_response.status_code == 200:
                img_data = BytesIO(img_response.content)
                img = Image(img_data, width=200, height=150)
                img.drawOn(pdf, 200, height - 480)  # Adjust position
                pdf.setFont("Helvetica", 10)
                pdf.drawString(220, height - 500, "Property Image")
        except Exception as e:
            pdf.drawString(100, height - 500, "Image could not be loaded.")

    # 🔹 **Footer**
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.setFillColor(colors.grey)
    pdf.drawString(200, 30, "Generated by Interior Leads System | © 2025")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    response.write(buffer.read())
    return response

class AddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """🔹 Get both Billing & Shipping addresses of the user"""
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """🔹 Add Billing or Shipping Address (Only one of each)"""
        address_type = request.data.get('address_type')

        # Ensure only one of each type
        if Address.objects.filter(user=request.user, address_type=address_type).exists():
            return Response({"error": f"{address_type.capitalize()} Address already exists. Use PUT to update."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """🔹 Update Billing or Shipping Address"""
        address_type = request.data.get('address_type')

        try:
            address = Address.objects.get(user=request.user, address_type=address_type)
        except Address.DoesNotExist:
            return Response({"error": f"{address_type.capitalize()} Address not found. Please create it first."},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)