from django.core.paginator import Paginator

NUMBER_OF_POSTS = 10


def get_page_obj(request, post_list):
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
