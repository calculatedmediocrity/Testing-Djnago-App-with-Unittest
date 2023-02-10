import shutil
import tempfile

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from . import constants as c
from ..utils import NUMBER_OF_POSTS
from ..models import User, Group, Post, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create(username='user1')
        cls.user2 = User.objects.create(username='user2')

        cls.image = SimpleUploadedFile(
            name=c.GIF_NAME,
            content=c.GIF_CONTENT,
            content_type=c.GIF_CONTENT_TYPE
        )

        cls.group = Group.objects.create(
            title=c.GROUP_TITLE,
            slug=c.GROUP_SLUG,
            description=c.GROUP_DESCRIPTION,
        )

        cls.post = Post.objects.create(
            author=cls.user1,
            text=c.POST_TEXT,
            group=cls.group,
        )

        cls.another_group = Group.objects.create(
            title=c.ANOTHER_GROUP_TITLE,
            slug=c.ANOTHER_GROUP_SLUG,
            description=c.ANOTHER_GROUP_DESCRIPTION,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def check_post_fields(self, post):
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.id, self.post.group.id)
        self.assertEqual(post.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """View-классы используют ожидаемые HTML-шаблоны."""
        templates_url_names = {
            reverse(c.URL_INDEX): c.TEMPLATE_INDEX,
            reverse(c.URL_GROUP, args=(self.group.slug,)):
                c.TEMPLATE_GROUP,
            reverse(c.URL_PROFILE, args=(self.user1.username,)):
                c.TEMPLATE_PROFILE,
            reverse(c.URL_POST_DETAIL, args=(self.post.pk,)):
                c.TEMPLATE_POST_DETAIL,
            reverse(c.URL_POST_CREATE): c.TEMPLATE_POST_CREATE,
            reverse(c.URL_POST_EDIT, args=(self.post.pk,)):
                c.TEMPLATE_POST_CREATE,
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client1.get(reverse(c.URL_INDEX))
        self.check_post_fields(response.context['page_obj'][0])

    def test_group_list_page_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client1.get(
            reverse(c.URL_GROUP, kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_fields(response.context['page_obj'][0])

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client1.get(
            reverse(c.URL_PROFILE, kwargs={
                'username': self.post.author.username
            })
        )
        self.assertEqual(response.context['user_profile'], self.user1)
        self.check_post_fields(response.context['page_obj'][0])

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client1.get(
            reverse(
                c.URL_POST_DETAIL, kwargs={'post_id': self.post.pk})
        )
        self.check_post_fields(response.context['post'])

    def test_create_post_page_shows_correct_context(self):
        """Шаблон создания поста сформирован с правильным контекстом."""
        response = self.authorized_client1.get(reverse(c.URL_POST_CREATE))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_shows_correct_context(self):
        """Шаблон редактирования поста сформирован с правильным контекстом."""
        response = self.authorized_client1.get(
            reverse(c.URL_POST_EDIT, kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_home_group_list_profile_pages(self):
        """Появление поста на главной странице, на странице группы,
        в профайле пользователя.
        """
        templates_url_names = (
            reverse(c.URL_INDEX),
            reverse(c.URL_GROUP, kwargs={'slug': self.group.slug}),
            reverse(
                c.URL_PROFILE, kwargs={'username': self.post.author.username}
            ),
        )
        for url in templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_client1.get(url)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_not_in_second_group(self):
        """Пост не находится на станице другой группы"""
        response = self.authorized_client1.get(
            reverse(
                c.URL_GROUP,
                kwargs={'slug': self.another_group.slug}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_post_comment_guest_user(self):
        """Добавление комментария неавторизованным пользователем"""
        count_comments = Comment.objects.count()
        self.guest_client.post(
            reverse(c.URL_POST_ADD_COMMENT, args=[self.post.id]),
            data={'text': c.COMMENT_TEXT}
        )
        self.assertEqual(count_comments, Comment.objects.count())

    def test_post_comment_authorized_user(self):
        """Добавление комментария авторизованным пользователем"""
        count_comments = Comment.objects.count()
        self.authorized_client2.post(
            reverse(c.URL_POST_ADD_COMMENT, args=[self.post.id]),
            data={'text': c.COMMENT_TEXT}
        )
        self.assertEqual(count_comments + 1, Comment.objects.count())

    def test_cache(self):
        """Проверка кеширования"""
        response = self.authorized_client1.get(reverse(c.URL_INDEX))
        Post.objects.filter(text=c.POST_TEXT, author=self.user1).delete()
        self.assertEqual(response.context.get('page_obj')[0], self.post)
        cache.clear()
        self.assertIsNot(response.context.get('page_obj')[0], self.post)

    def test_post_profile_follow(self):
        """Проверка, возможно ли подписаться на автора поста."""
        self.authorized_client1.get(
            reverse('posts:profile_follow', kwargs={'username': 'author'})
        )
        self.assertTrue(
            Follow.objects.filter(
                author=self.author,
                user=self.user1,
            ).exists(),
        )

    def test_post_profile_unfollow(self):
        """Проверка, возможно ли отписаться от автора поста."""
        self.authorized_client2.get(
            reverse('posts:profile_unfollow', kwargs={'username': 'author'})
        )
        self.assertFalse(
            Follow.objects.filter(
                author=self.author,
                user=self.user2
            ).exists()
        )

    def test_post_follow_index_follower(self):
        """Проверка, находится ли новый пост в ленте подписчика."""
        response_follower = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        post_follow = response_follower.context.get('page_obj')[0]
        self.assertEqual(post_follow, self.post)

    def test_post_follow_index_unfollower(self):
        """Проверка находится ли пост в ленте не подписчика."""
        response_unfollower = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        post_unfollow = response_unfollower.context.get('page_obj')
        self.assertEqual(post_unfollow.object_list.count(), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username=c.USERNAME
        )
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)

        cls.group = Group.objects.create(
            title=c.GROUP_TITLE,
            slug=c.GROUP_SLUG,
            description=c.GROUP_DESCRIPTION,
        )

        cls.post_qty = c.TOTAL_POST_QTY
        Post.objects.bulk_create(
            [Post(
                author=cls.user,
                text=f'{c.POST_TEXT} {post}',
                group=cls.group
            )for post in range(cls.post_qty)]
        )

        cls.templates_url_names = [
            reverse(c.URL_INDEX),
            reverse(c.URL_GROUP, kwargs={'slug': cls.group.slug}),
            reverse(c.URL_PROFILE, kwargs={'username': cls.user,
                                           }),
        ]

    def setUp(self):
        cache.clear()

    def test_paginator(self):
        """Проверка пагинатора"""
        for url in self.templates_url_names:
            with self.subTest(url=url):
                for page in (1, 2):
                    if page == 1:
                        self.assertEqual(
                            len(self.authorized_user.get(url).context.get('page_obj')),
                            NUMBER_OF_POSTS
                        )
                    else:
                        self.assertEqual(
                            len(self.authorized_user.get(
                                url,
                                {'page': page}
                            ).context.get('page_obj')),
                            c.POST_QTY_ON_SECOND_PAGE
                        )
