from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import *


# Create your views here.
@login_required
def user_bookmarks(request):
    bookmarks = JobBookmark.objects.filter(user=request.user).select_related('job__company')

    paginator = Paginator(bookmarks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'jobs/user_bookmarks.html', context)


@login_required
def toggle_bookmark(request, job_id):
    job = Job.objects.get(id=job_id, is_active=True)
    bookmark, created = JobBookmark.objects.get_or_create(user=request.user, job=job)

    if created:
        messages.success(request, f'Job "{job.title}" bookmarked successfully!')
        bookmarked = True
    else:
        bookmark.delete()
        messages.success(request, f'Job "{job.title}" removed from bookmarks!')
        bookmarked = False

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'bookmarked': bookmarked})

    return redirect('job_detail', slug=job.slug)
