from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from . import constants as c
from ..models import Group, Post, User


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.creator = User.objects.create_user(
            username=c.USERNAME
        )

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

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        self.authorized_creator = Client()
        self.authorized_creator.force_login(self.creator)

        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.post.group.id,
        }
        response = self.authorized_creator.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(text=c.POST_TEXT).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        ANOTHER_GROUP_TITLE = 'Другая тестовая группа'
        ANOTHER_GROUP_SLUG = 'new-slug'
        ANOTHER_GROUP_DESCRIPTION = 'Новое описание'
        ANOTHER_POST_TEXT = 'Новый текст'

        group_2 = Group.objects.create(
            title=ANOTHER_GROUP_TITLE,
            slug=ANOTHER_GROUP_SLUG,
            description=ANOTHER_GROUP_DESCRIPTION,
        )

        self.authorized_creator = Client()
        self.authorized_creator.force_login(self.creator)

        form_data = {
            'text': ANOTHER_POST_TEXT,
            'group': group_2.pk,
        }

        response = self.authorized_creator.post(
            reverse('posts:edit', kwargs={'post_id': self.post.group.id}),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post.group.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, ANOTHER_POST_TEXT)
