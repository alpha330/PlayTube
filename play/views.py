from django.shortcuts import render, HttpResponse, redirect
from django.db.models import Q
from django.contrib.auth import login, logout
from .models import Video, Channel, History
from .forms import VideoUploadForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
import os

# Create your views here.


def loginPage(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # redirect to the page user was trying to access before logging in
            next = request.POST.get('next')
            return redirect(next or 'play:home')
        else:
            return redirect('play:login')

    form = AuthenticationForm(request)
    context = {'form': form}
    return render(request, 'play/login_register.html', context)


def logoutPage(request):
    logout(request)
    return redirect('play:home')


def home(request):
    # check if play_video table is empty without using count()
    if Video.objects.exists():
        videos = Video.objects.all()
        # shuffle the videos
        videos = videos.order_by('?')

        paginator = Paginator(videos, per_page=15)  # Show 15 videos per page.

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        videos = {'videos': page_obj}
        return render(request, 'play/home.html', videos)
    else:
        return render(request, 'play/404.html', {'info': 'No videos found'}, status=404)

@login_required
def profile(request):
    channel = request.user.channel
    videos = Video.objects.filter(channel=channel)
    return render(request, 'play/profile.html', {'channel': channel, 'videos': videos})

def results(request):
    query = request.GET.get('search_query')
    if query is None:
        return redirect('play:home')

    movies = Video.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(genre__icontains=query) |
        Q(series_name__icontains=query) |
        Q(channel__name__icontains=query) |
        Q(channel__handle__icontains=query) |
        Q(channel__user__username__icontains=query) |
        Q(release_year__icontains=query)
    )
    if movies.count() == 0:
        # show no results found page
        info = {'info': 'No results found'}
        return render(request, 'play/404.html', info, status=404)
    movies = {'movies': movies, 'search_query': query}
    return render(request, 'play/results.html', movies)


@login_required
def videoUpload(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.channel = request.user.channel
            video.save()
            return JsonResponse({'success': True, 'redirect_url': reverse('play:home')})
        else:
            return JsonResponse({'success': False})
    form = VideoUploadForm()
    return render(request, 'play/upload.html', {'form': form})


def watch(request):
    video_id = request.GET.get('v')
    channel_id = request.GET.get('ab_channel')
    t = request.GET.get('t')
    t = 0 if t is None else t
    if video_id is None and channel_id is None:
        info = {'info': 'This video isn\'t available anymore'}
        return render(request, 'play/404.html', info, status=404)
    try:
        video = Video.objects.get(video_id=video_id)
        channel_id = video.channel.channel_id if channel_id is None else channel_id
        channel = Channel.objects.get(
            channel_id=channel_id) if channel_id is not None else None

        # initialize history object
        # check if user is logged in
        if request.user.is_authenticated:
            history, created = History.objects.get_or_create(
                channel=request.user.channel,
                video=video,
                defaults={'timestamp': 0})
            # if t is None, then set t to the last viewed timestamp if user watched the video before
            t = history.timestamp if t is 0 else t
            history.save()

        stream_path = os.path.join(os.path.dirname(
            video.video_file.path), 'playlist.m3u8')
        return render(request, 'play/watch.html', {'video_id': video_id, 'channel_id': channel_id, 't': t, 'movie': video, 'channel': channel, 'stream_path': stream_path, 'domain_name': settings.DOMAIN_NAME, 'http_protocol': 'https' if settings.USE_HTTPS else 'http'})

    except Channel.DoesNotExist:
        info = {'info': 'This video isn\'t available anymore'}
        return render(request, 'play/404.html', info, status=404)
    except Video.DoesNotExist:
        info = {'info': 'This video isn\'t available anymore'}
        return render(request, 'play/404.html', info, status=404)


def channel_via_handle(request, handle):
    # search the channel handle in the database, else return 404
    try:
        channel = Channel.objects.get(handle=handle)
    except Channel.DoesNotExist:
        info = {'info': 'Channel does not exist'}
        return render(request, 'play/404.html', info, status=404)
    videos = Video.objects.filter(channel=channel)
    return render(request, 'play/profile.html', {'channel': channel, 'videos': videos})


def channel_via_id(request, channel_id):
    # search the channel id in the database, else return 404
    try:
        channel = Channel.objects.get(channel_id=channel_id)
    except Channel.DoesNotExist:
        info = {'info': 'Channel does not exist'}
        return render(request, 'play/404.html', info, status=404)
    videos = Video.objects.filter(channel=channel)
    return render(request, 'play/profile.html', {'channel': channel, 'videos': videos})


@login_required(login_url='play:login')
def history(request):
    # get user's watch history
    channel = request.user.channel
    history = History.objects.filter(channel=channel)
    history = history.order_by('-last_viewed')
    return render(request, 'play/history.html', {'history': history})


# custom error pages
# handle custom 404 error
def error_404(request, exception):
    return render(request, 'play/404.html', {'info': 'The requested url was not found on the server'}, status=404)
