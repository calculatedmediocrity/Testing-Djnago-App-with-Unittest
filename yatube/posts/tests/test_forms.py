from http import HTTPStatus
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from . import constants as c
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.image = SimpleUploadedFile(
            name=c.GIF_NAME,
            content=c.GIF_CONTENT,
            content_type=c.GIF_CONTENT_TYPE
        )

        cls.creator = User.objects.create_user(
            username=c.USERNAME
        )

        cls.group = Group.objects.create(
            title=c.GROUP_TITLE,
            slug=c.GROUP_SLUG,
            description=c.GROUP_DESCRIPTION,
        )

        cls.another_group = Group.objects.create(
            title=c.ANOTHER_GROUP_TITLE,
            slug=c.ANOTHER_GROUP_SLUG,
            description=c.ANOTHER_GROUP_DESCRIPTION,
        )

        cls.post = Post.objects.create(
            author=cls.creator,
            text=c.POST_TEXT,
            group=cls.group,
            image=cls.image
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        self.authorized_creator = Client()
        self.authorized_creator.force_login(self.creator)

        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.post.group.id,
            'image': self.post.image,
        }
        response = self.authorized_creator.post(
            reverse(c.URL_POST_CREATE),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                c.URL_PROFILE,
                kwargs={'username': self.post.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=c.POST_TEXT,
                image=form_data['image']
            ).exists(),
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        self.authorized_creator = Client()
        self.authorized_creator.force_login(self.creator)

        form_data = {
            'text': c.ANOTHER_POST_TEXT,
            'group': self.another_group.pk,
        }

        response = self.authorized_creator.post(
            reverse(c.URL_POST_EDIT, kwargs={'post_id': self.post.group.id}),
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post.group.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, c.ANOTHER_POST_TEXT)
