from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from django.shortcuts import redirect

from Emusic_app.models import Artist, Notification, Song

from .forms import SearchForm
from django.db.models import Q 



# Create your views here.
def home(request):
    return render(request,'home.html')

def user_login(request): 
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    return render(request, "login.html")

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if User.objects.filter(username=username):
             messages.error(request, "Username already exist! Please try another username!")
             return redirect('signup')
        
        if User.objects.filter(email=email):
             messages.error(request, "Email alrady Registered")
             return redirect('signup')
        
        if len(username)>15:
             messages.error(request, "Username must be under 15 characters")
            
        if pass1 != pass2:
             messages.error(request, "Password didn't match")

        if not username.isalpha():
             messages.error(request, "Username must be Alpha-Numeric!")
             return redirect('signup')
    
        myuser = User.objects.create_user(username,email,pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()
        messages.success(request, "Your account has been created succesfully.")
        return redirect('login')

    return render(request,"signup.html")

def signout(request):
        logout(request)
        messages.success(request, "Logged out Successfully")
        return redirect('home')



def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def profile(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    return render(request, 'profile.html')

def subscription(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    return render(request, 'subscription_plans.html')

def notifications(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

def dashboard(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    return render(request, 'dashboard.html')

from django.conf import settings
from django.shortcuts import render, redirect
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

def search(request):
    query = request.GET.get('query', '')
    if query:
        # Construct Spotify search URL
        spotify_url = f"https://open.spotify.com/search/{query}"
        return redirect(spotify_url)
    return redirect('dashboard')

# def songs_view(request):
#     # Get the Spotify client
#     sp = get_spotify_client()
    
#     # Fetch data from Spotify (for example, popular tracks)
#     results = sp.current_user_top_tracks(limit=10)  # Fetch top 10 tracks
#     tracks = results['items']

#     return render(request, 'songs.html', {'tracks': tracks})

# def callback(request):
#     # Spotify OAuth callback handler
#     sp_oauth = SpotifyOAuth(client_id=settings.SPOTIPY_CLIENT_ID,
#                              client_secret=settings.SPOTIPY_CLIENT_SECRET,
#                              redirect_uri=settings.SPOTIPY_REDIRECT_URI,
#                              scope="user-library-read")
#     token_info = sp_oauth.get_access_token(request.GET['code'])
#     sp = Spotify(auth=token_info['access_token'])

#     return redirect('/songs/')

#def search(request):
#    return render(request,'search.html')





def profilechange(request):
    if request.method == "POST":
        
        usernamechange = request.POST['username']
        emailchange = request.POST['email']
        user = User.objects.get(username=request.user.username)
        user.username=usernamechange
        user.email=emailchange
        user.save()
        notifications = Notification.objects.create(user=user,message="Your profile has been successfully updated!")
        
        notifications.save()
        print(notifications)
        return redirect(request.path)
    return render(request, 'profile.html')




# import requests
# from django.shortcuts import redirect, render
# from django.conf import settings

def spotify_dashboard(request):
    """Displays a simple Spotify dashboard."""
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return redirect('spotify_login')

    # Fetch user's Spotify data
    user_profile_url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(user_profile_url, headers=headers)
    user_data = user_response.json()

    redirect_url = f"https://open.spotify.com?access_token={access_token}"
    return HttpResponseRedirect(redirect_url)

def spotify_login(request):
    """Redirects to Spotify for user authorization."""
    scope = "user-read-private user-read-email"  # Add scopes as required
    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={settings.SPOTIFY_CLIENT_ID}&response_type=code"
        f"&redirect_uri={settings.SPOTIFY_REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

def spotify_callback(request):
    """Handles Spotify callback and fetches an access token."""
    code = request.GET.get('code')
    if not code:
        return render(request, 'error.html', {"message": "Authorization failed."})

    # Exchange the authorization code for an access token
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    response_data = response.json()

    access_token = response_data.get('access_token')
    if not access_token:
        return render(request, 'error.html', {"message": "Failed to get access token."})
    print(access_token)
    # Save the access token in the session
    request.session['spotify_access_token'] = access_token
    return redirect('spotify_dashboard')  # Redirect to a page to browse Spotify content


def search(request):
    query = request.GET.get('query', '')
    results = None
    print("/n"+query+"/n")
    # Set up the Spotify API client
    return redirect(f'https://open.spotify.com/search/{query}')
    '''sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id='934b31cd0e5b400c9fb02c9c6ce1d2a3',
        client_secret='06eeaed8b19f4e618f7be6d9d0d33a98',
        redirect_uri='http://127.0.0.1:8000/spotify/callback/',
    ))

    if query:
        # Perform search for tracks and artists
        result_data = sp.search(q=query, limit=3, type='track,artist')

        results = {
            'songs': result_data['tracks']['items'],
            'artists': result_data['artists']['items'],
        }

    return render(request, 'search.html', {
        'query': query,
        'results': results
    })'''