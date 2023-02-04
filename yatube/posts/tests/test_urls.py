from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from . import constants as c
from ..models import User, Group, Post


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.creator = User.objects.create_user(
            username=c.CREATOR_USERNAME
        )
        cls.authorized_creator = Client()
        cls.authorized_creator.force_login(cls.creator)
        cls.viewer = User.objects.create_user(
            username=c.VIEWER_USERNAME
        )
        cls.authorized_viewer = Client()
        cls.authorized_viewer.force_login(cls.viewer)

        cls.group = Group.objects.create(
            title=c.GROUP_TITLE,
            slug=c.GROUP_SLUG,
            description=c.GROUP_DESCRIPTION,
        )

        cls.post = Post.objects.create(
            author=cls.creator,
            group=cls.group,
            text=c.POST_TEXT,
        )

    def test_public_urls_exist_at_desired_location(self):
        """Доступ неавторизованных пользователей"""
        public_url_names = {
            reverse(c.URL_INDEX),
            reverse(c.URL_GROUP, args=(self.group.slug,)),
            reverse(c.URL_PROFILE, args=(self.creator.username,)),
            reverse(c.URL_POST_DETAIL, args=(self.post.pk,)),
            c.URL_UNEXISTING_PAGE,
        }
        for url in public_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                if url == c.URL_UNEXISTING_PAGE:
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.NOT_FOUND
                    )
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_urls_exist_at_desired_location(self):
        """Доступ авторизованных пользователей"""
        private_url_names = {
            reverse(c.URL_POST_CREATE),
            reverse(c.URL_POST_EDIT, args=(self.post.pk,)),
        }
        for url in private_url_names:
            with self.subTest(url=url):
                response = self.authorized_creator.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirects_anonymous(self):
        """Перенаправление неавторизованного пользователя
        со страницы create.
        """
        response = self.guest_client.get(
            reverse(c.URL_POST_CREATE),
            follow=True
        )
        self.assertRedirects(response, c.URL_REDIRECT_FROM_CREATE)

    def test_edit_url_redirects_anonymous(self):
        """Перенаправление неавторизованного пользователя со страницы edit."""
        response = self.guest_client.get(
            reverse(c.URL_POST_EDIT, args=(self.post.pk,)),
            follow=True
        )
        self.assertRedirects(response, c.URL_REDIRECT_FROM_EDIT)

    def test_edit_url_redirects_authorised(self):
        """Перенаправление авторизованного пользователя со страницы edit."""
        response = self.authorized_viewer.get(
            reverse(c.URL_POST_EDIT, args=(self.post.pk,)),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(c.URL_POST_DETAIL, args=(self.post.pk,))
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
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

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_creator.get(url)
                self.assertTemplateUsed(response, template)
