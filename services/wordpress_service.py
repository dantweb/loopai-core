import os
import wordpress

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, EditPost, GetPosts, GetPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc.methods.taxonomies import GetTerms
from wordpress_xmlrpc.methods.users import GetUserInfo
from wordpress_xmlrpc.methods import posts
from wordpress_xmlrpc.compat import xmlrpc_client
from dotenv import load_dotenv

load_dotenv()


class WordPressService:

    def __init__(self, wp_url=None, wp_username=None, wp_password=''):
        self.client = Client(wp_url, wp_username, wp_password)
        self.wp_posts = self.get_all_posts()

    def add_post(self, data):
        post = WordPressPost()
        post.title = data.get('title', '')
        post.content = data.get('content', '')
        post.terms_names = data.get('terms_names', {})
        post.post_status = data.get('post_status', 'draft')
        post.id = self.client.call(NewPost(post))
        return post.id

    def upload_media(self, file_path):
        data = {
            'name': os.path.basename(file_path),
            'type': 'image/jpeg',
        }
        with open(file_path, 'rb') as img:
            data['bits'] = xmlrpc_client.Binary(img.read())
        response = self.client.call(UploadFile(data))
        return response['id']

    def update_post(self, post_id, data):
        post = self.client.call(GetPost(post_id))
        post.title = data.get('title', post.title)
        post.content = data.get('content', post.content)
        post.post_status = data.get('post_status', post.post_status)
        self.client.call(EditPost(post_id, post))

    def set_feature_image(self, post_id, image_id):
        post = self.client.call(GetPost(post_id))
        post.thumbnail = image_id
        self.client.call(EditPost(post_id, post))

    def get_post_id_by_meta(self, field_name, field_value):
        for post in self.wp_posts:
            for field in post.custom_fields:
                if field['key'] == field_name and field['value'] == field_value:
                    return post.id

        return None

    def set_feature_image_by_icd10code(self, icd10code, image_id):
        post_id = self.get_post_id_by_meta('icd10code', icd10code)
        if post_id:
            self.set_feature_image(post_id, image_id)
        else:
            return "no post found"

    def get_all_posts(self):
        self.wp_posts = self.client.call(GetPosts({'number': 1000}))
        return self.wp_posts# Adjust number as needed

    def update_post_meta(self, post_id, meta_key, meta_value):
        post = self.client.call(GetPost(post_id))
        post.custom_fields = post.custom_fields or []

        # Check if the meta key already exists and update it
        for field in post.custom_fields:
            if field['key'] == meta_key:
                field['value'] = meta_value
                break
        else:
            # Meta key does not exist, create a new one
            post.custom_fields.append({
                'key': meta_key,
                'value': meta_value
            })

        self.client.call(EditPost(post_id, post))

    def reload_local_posts(self):
        self.wp_posts = self.get_all_posts()
