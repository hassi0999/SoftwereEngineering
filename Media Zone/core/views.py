import random
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import MediaItem, SearchHistory, User
from core.serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
# from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import urllib.parse


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "This is a protected view"})


def home_view(request):
    return render(request, "login.html")


def login_view(request):
    return render(request, 'login.html') 


def main(request):
    return render(request, "main.html")


def user_list(request):
    users = User.objects.all()  # Fetch all users from the database
    return render(request, "user_list.html", {"users": users})


def delete_search(request, search_id):
    if request.method == "POST":
        try:
            search = SearchHistory.objects.get(id=search_id)
            search.delete()
        except SearchHistory.DoesNotExist:
            pass
    return redirect(request.META.get("HTTP_REFERER", "media_search/"))


def update_search(request, search_id):
    if request.method == "POST":
        search = get_object_or_404(SearchHistory, id=search_id)
        query = request.POST.get("query")
        media_type = request.POST.get("media_type")

        # Example: Update the query and media_type
        if query:
            search.query = query
        if media_type:
            search.media_type = media_type

        search.save()

    return redirect(request.META.get("HTTP_REFERER", "media_search/"))


def search_history_view(request):
    user_id = request.GET.get("user_id")
    search_history = []

    if user_id:
        try:
            user = User.objects.get(id=user_id)
            search_history = SearchHistory.objects.filter(user=user).order_by(
                "-searched_at"
            )
        except User.DoesNotExist:
            pass

    return render(request, "search_history.html", {"search_history": search_history})


@api_view(["POST", "GET"])
def signup(request):
    if request.method == "POST":
        print("SIGNUP VIEW HIT")

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": 200, "message": "User created successfully"}, status=200
            )
        else:
            return Response({"status": 400, "message": serializer.errors}, status=400)

    else:
        return render(request, "signup.html")


# User Login API View
@api_view(["POST", "GET"])
def login(request):
    print("loginapo sajdjsa")
    if request.method == "POST":
        user_email = request.data.get("user_email")
        user_password = request.data.get("user_password")

        # Check if email and password are provided
        if not user_email or not user_password:
            return Response(
                {"status": 400, "message": "Please provide both email and password"},
                status=400,
            )

        try:
            # Check if user exists
            user = User.objects.get(user_email=user_email)

            # Check if password is correct
            if check_password(user_password, user.user_password):
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response(
                    {
                        "status": 200,
                        "message": "Login successful",
                        "access_token": access_token,
                        "user_id": user.id,
                    },
                    status=200,
                )
            else:
                return Response(
                    {"status": 401, "message": "Invalid credentials"}, status=401
                )

        except User.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

    else:
        return render(request, "login.html")


@api_view(["PUT", "DELETE"])
def update_delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)

        # Anyone logged in can update or delete users now
        if request.method == "PUT":
            user_name = request.data.get("user_name")
            user_email = request.data.get("user_email")
            user_password = request.data.get("user_password")

            if user_name:
                user.user_name = user_name
            if user_email:
                user.user_email = user_email
            if user_password:
                user.user_password = make_password(user_password)

            user.save()

            return Response({"status": 200, "message": "User updated successfully"})

        elif request.method == "DELETE":
            user.delete()
            return Response({"status": 200, "message": "User deleted successfully"})

    except User.DoesNotExist:
        return Response({"status": 404, "message": "User not found"})
    except Exception as e:
        return Response({"status": 500, "message": str(e)})


def media_search(request):
    query = request.GET.get("query", "")
    media_type = request.GET.get("media_type", "image")
    user_id = request.GET.get("user_id")

    print("Query:", query)
    print("user_id", user_id)

    # Encode the query properly to handle spaces and special characters
    encoded_query = urllib.parse.quote(query)
    page = random.randint(1, 5)

    base_url = "https://api.openverse.org/v1"
    if media_type == "image":
        url = f"{base_url}/images?q={encoded_query}&page={page}&license_type=all&size=medium"
    else:
        url = f"{base_url}/audio?q={encoded_query}&page={page}&license_type=all"

    print("Fetching URL:", url)
    response = requests.get(url, headers={"User-Agent": "MediaSearchApp/1.0"})

    if response.status_code != 200:
        return render(
            request,
            "media_search.html",
            {
                "media_items": [],
                "query": query,
                "media_type": media_type,
                "error": "Failed to fetch media items",
            },
        )

    data = response.json()
    media_items = data.get("results", [])
    # Save search history and media items
    if user_id and query:
        try:
            user = User.objects.get(id=user_id)
            SearchHistory.objects.create(user=user, query=query, media_type=media_type)

            for item in media_items:
                MediaItem.objects.create(
                    user=user,
                    query=query,
                    media_type=media_type,
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    thumbnail=item.get("thumbnail", ""),
                )
        except User.DoesNotExist:
            print("User not found!")

    return render(
        request,
        "media_search.html",
        {"media_items": media_items, "query": query, "media_type": media_type},
    )
