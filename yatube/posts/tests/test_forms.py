from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post, User


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.creator = User.objects.create_user(
            username='creator_name'
        )
        cls.authorized_creator = Client()
        cls.authorized_creator.force_login(cls.creator)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.creator,
            text='Тестовый пост',
            group=cls.group,
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
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
            Post.objects.filter(text='Тестовый пост').exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {
            'text': self.post.text,
            'group': self.post.group.id,
        }
        self.authorized_creator.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.group.id)
        self.authorized_creator.get(f'/posts/{post.pk}/edit/')
        form_data = {
            'text': 'Измененный текст',
            'group': self.post.group.id,
        }
        response = self.authorized_creator.post(
            reverse('posts:edit', kwargs={'post_id': self.post.group.id}),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post.group.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, 'Измененный текст')
