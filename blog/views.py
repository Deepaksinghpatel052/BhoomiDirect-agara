from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from core.seo import absolute, crumbs

from .models import Category, Post


def post_list(request, category_slug=None):
    posts = Post.objects.filter(is_published=True).select_related("category")
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(category=category)
    page = Paginator(posts, 9).get_page(request.GET.get("page"))
    trail = [("Blog", "/blog/")] + ([(category.name, None)] if category else [])
    if not category:
        trail = [("Blog", None)]
    return render(
        request,
        "blog/list.html",
        {
            "page_obj": page,
            "category": category,
            "categories": Category.objects.all(),
            "breadcrumbs": crumbs(*trail),
            "page_title": f"{category.name} Articles" if category else "Land Selling Guides for Agra Owners",
            "meta_description": "Guides on selling land in Agra: documents, Khatauni, circle rates, mutation and more.",
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("category"), slug=slug, is_published=True)
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post.title,
        "description": post.seo_description,
        "datePublished": post.published_at.isoformat(),
        "dateModified": post.updated_at.isoformat(),
        "author": {"@type": "Organization", "name": post.author_name},
        "publisher": {"@type": "Organization", "name": settings.SITE_NAME},
        "mainEntityOfPage": absolute(post.get_absolute_url()),
    }
    if post.cover_image:
        schema["image"] = request.build_absolute_uri(post.cover_image.url)
    return render(
        request,
        "blog/detail.html",
        {
            "post": post,
            "related": Post.objects.filter(is_published=True).exclude(pk=post.pk)[:3],
            "breadcrumbs": crumbs(("Blog", "/blog/"), (post.title, None)),
            "schemas": [schema],
        },
    )
