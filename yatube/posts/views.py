from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User
from .forms import PostForm
from .utils import get_page_obj


def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': get_page_obj(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_page_obj(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    post_list = (
        Post.objects.select_related("author", "group")
        .filter(author=user_profile).all()
    )
    context = {
        'user_profile': user_profile,
        'page_obj': get_page_obj(request, post_list),
    }

    return render(
        request,
        'posts/profile.html',
        context
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {'post': post}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        context = {'form': form}
        return render(request, 'posts/create_post.html', context)
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', new_post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': True}
    return render(request, 'posts/create_post.html', context)
