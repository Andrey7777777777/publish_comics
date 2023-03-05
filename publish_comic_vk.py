import random
import os
import requests
from environs import Env


def get_random_comic_number():
    url_comics = 'https://xkcd.com/info.0.json'
    response = requests.get(url_comics)
    response.raise_for_status()
    comics_id = random.randint(1, response.json()['num'])
    return comics_id


def download_random_image(comics_id):
    url_comics = f'https://xkcd.com/{comics_id}/info.0.json'
    response = requests.get(url_comics)
    response.raise_for_status()
    decoded_response = response.json()
    comics_images = decoded_response['img']
    message = decoded_response['alt']
    return comics_images, message


def download_images(filename, comics_images):
    response = requests.get(comics_images)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)


def get_upload_server_url(group_id, token, api_version):
    params = {
        'group_id': group_id,
        'access_token': token,
        'v': api_version
    }
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(url, params=params)
    response.raise_for_status()
    decoded_response = response.json()
    return decoded_response['response']['upload_url']


def send_photo(url, filename):
    with open(filename, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
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
    decoded_response = response.json()
    owner_id = decoded_response['response'][0]['owner_id']
    media_id = decoded_response['response'][0]['id']
    return owner_id, media_id


def post_comics(owner_id, media_id, group_id, token, message, api_version):
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


def main():
    api_version = 5.131
    env = Env()
    env.read_env()
    token = env.str("VK_TOKEN")
    group_id = env.str("VK_GROUP_ID")
    filename = "comic.png"
    comics_id = get_random_comic_number()
    comics_images, message = download_random_image(comics_id)
    download_images(filename, comics_images)
    upload_server_url = get_upload_server_url(group_id, token, api_version)
    photo_param, server_param, hash_param = send_photo(upload_server_url, filename)
    owner_id, media_id = save_photo(group_id, token, photo_param, server_param, hash_param, api_version)
    post_comics(owner_id, media_id, group_id, token, message, api_version)
    os.remove(filename)


if __name__ == '__main__':
    main()