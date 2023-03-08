import random
import os
import requests
from environs import Env


def get_random_comic_number():
    comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(comic_url)
    response.raise_for_status()
    comic_id = random.randint(1, response.json()['num'])
    return comic_id


def download_random_image(comic_id, filename):
    comic_url = f'https://xkcd.com/{comic_id}/info.0.json'
    response = requests.get(comic_url)
    response.raise_for_status()
    decoded_response = response.json()
    comic_image = decoded_response['img']
    message = decoded_response['alt']
    comic_response = requests.get(comic_image)
    comic_response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(comic_response.content)
    return message


def get_upload_server_url(group_id, token, api_version):
    params = {
        'group_id': group_id,
        'access_token': token,
        'v': api_version
    }
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(url, params=params)
    response.raise_for_status()
    raise_if_vk_error(response)
    decoded_response = response.json()
    return decoded_response['response']['upload_url']


def upload_photo(url, filename):
    with open(filename, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
    response.raise_for_status()
    raise_if_vk_error(response)
    decoded_response = response.json()
    photo_param = decoded_response['photo']
    server_param = decoded_response['server']
    hash_param = decoded_response['hash']
    return photo_param, server_param, hash_param


def save_photo(group_id, token, photo_param, server_param, hash_param, api_version):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {'group_id': group_id,
              'access_token': token,
              'photo': photo_param,
              'server': server_param,
              'hash': hash_param,
              'v': api_version
              }
    response = requests.post(url, params=params)
    response.raise_for_status()
    raise_if_vk_error(response)
    decoded_response = response.json()
    owner_id = decoded_response['response'][0]['owner_id']
    media_id = decoded_response['response'][0]['id']
    return owner_id, media_id


def post_comic(owner_id, media_id, group_id, token, message, api_version):
    url = 'https://api.vk.com/method/wall.post'
    attachments = f'photo{owner_id}_{media_id}'
    params = {'owner_id': f'-{group_id}',
              'access_token': token,
              'from_group': 1,
              'attachments': attachments,
              'message': message,
              'v': api_version
              }
    response = requests.post(url, params=params)
    response.raise_for_status()
    raise_if_vk_error(response)


class VKError(Exception):
    def __init__(self, decoded_response):
        self.error_msg = decoded_response['error']['error_msg']

    def __str__(self):
        return self.error_msg


def raise_if_vk_error(response):
    vk_decoded_response = response.json()
    if vk_decoded_response.get('error'):
        raise VKError(vk_decoded_response)



def main():
    api_version = 5.131
    env = Env()
    env.read_env()
    token = env.str("VK_TOKEN")
    group_id = env.str("VK_GROUP_ID")
    filename = "comic.png"
    try:
        comic_id = get_random_comic_number()
        message = download_random_image(comic_id,filename)
        upload_server_url = get_upload_server_url(group_id, token, api_version)
        photo_param, server_param, hash_param = upload_photo(upload_server_url, filename)
        owner_id, media_id = save_photo(group_id, token, photo_param, server_param, hash_param, api_version)
        post_comic(owner_id, media_id, group_id, token, message, api_version)
    finally:
        os.remove(filename)


if __name__ == '__main__':
    main()