from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from . import constants as c
from ..utils import NUMBER_OF_POSTS
from ..models import User, Group, Post


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.creator = User.objects.create_user(
            username=c.CREATOR_USERNAME
        )
        cls.authorized_creator = Client()
        cls.authorized_creator.force_login(cls.creator)

        cls.group = Group.objects.create(
            title=c.GROUP_TITLE,
            slug=c.GROUP_SLUG,
            description=c.GROUP_DESCRIPTION,
        )

        cls.post = Post.objects.create(
            author=cls.creator,
            text=c.POST_TEXT,
            group=cls.group,
        )

        cls.another_group = Group.objects.create(
            title=c.ANOTHER_GROUP_TITLE,
            slug=c.ANOTHER_GROUP_SLUG,
            description=c.ANOTHER_GROUP_DESCRIPTION,
        )

    def check_post_fields(self, post):
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.id, self.post.group.id)

    def test_pages_uses_correct_template(self):
        """View-классы используют ожидаемые HTML-шаблоны."""
        templates_url_names = {
            reverse(c.URL_INDEX): c.TEMPLATE_INDEX,
            reverse(c.URL_GROUP, args=(self.group.slug,)):
                c.TEMPLATE_GROUP,
            reverse(c.URL_PROFILE, args=(self.creator.username,)):
                c.TEMPLATE_PROFILE,
            reverse(c.URL_POST_DETAIL, args=(self.post.pk,)):
                c.TEMPLATE_POST_DETAIL,
            reverse(c.URL_POST_CREATE): c.TEMPLATE_POST_CREATE,
            reverse(c.URL_POST_EDIT, args=(self.post.pk,)):
                c.TEMPLATE_POST_CREATE,
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_creator.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_creator.get(reverse(c.URL_INDEX))
        self.check_post_fields(response.context['page_obj'][0])

    def test_group_list_page_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse(c.URL_GROUP, kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_fields(response.context['page_obj'][0])

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse(c.URL_PROFILE, kwargs={
                'username': self.post.author.username
            })
        )
        self.assertEqual(response.context['user_profile'], self.creator)
        self.check_post_fields(response.context['page_obj'][0])

    def test_post_detail_page_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_creator.get(
            reverse(
                c.URL_POST_DETAIL, kwargs={'post_id': self.post.pk})
        )
        self.check_post_fields(response.context['post'])

    def test_create_post_page_shows_correct_context(self):
        """Шаблон создания поста сформирован с правильным контекстом."""
        response = self.authorized_creator.get(reverse(c.URL_POST_CREATE))
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
        response = self.authorized_creator.get(
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
                response = self.authorized_creator.get(url)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_not_in_second_group(self):
        """Пост не находится на станице другой группы"""
        response = self.authorized_creator.get(
            reverse(
                c.URL_GROUP,
                kwargs={'slug': self.another_group.slug}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 0)


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
            reverse(c.URL_PROFILE, kwargs={'username': cls.user}),
        ]

    def test_second_page_contains_three_records(self):
        """Проверка пагинатора"""
        for url in self.templates_url_names:
            with self.subTest(url=url):
                for page in (1, 2):
                    if page == 1:
                        self.assertEqual(
                            len(self.client.get(url).context.get('page_obj')),
                            NUMBER_OF_POSTS
                        )
                    else:
                        self.assertEqual(
                            len(self.client.get(
                                url,
                                {'page': page}
                            ).context.get('page_obj')),
                            c.POST_QTY_ON_SECOND_PAGE
                        )
