import os
import subprocess
from functools import lru_cache
from pathlib import Path

from module.downloader import download_path
import requests
import bs4
from module.network import get_finial_url
import logging


logger = logging.getLogger(__name__)


@lru_cache(1)
def get_firmware_infos():
    base_url = 'https://archive.org/download/nintendo-switch-global-firmwares/'
    resp = requests.get(get_finial_url(base_url))
    soup = bs4.BeautifulSoup(resp.text, features="html.parser")
    a_tags = soup.select('#maincontent > div > div > pre > table > tbody > tr > td > a')
    archive_versions = []
    for a in a_tags:
        name = a.text
        if name.startswith('Firmware ') and name.endswith('.zip'):
            size = a.parent.next_sibling.next_sibling.next_sibling.next_sibling.text
            version = name[9:-4]
            version_num = 0
            for num in version.split('.'):
                version_num *= 100
                version_num += int(''.join(ch for ch in num if ch.isdigit()))
            archive_versions.append({
                'name': name,
                'version': version,
                'size': size,
                'url': base_url + a.attrs['href'],
                'version_num': version_num,
            })
    archive_versions = sorted(archive_versions, key=lambda x: x['version_num'], reverse=True)
    return archive_versions


@lru_cache(1)
def get_keys_info():
    resp = requests.get('https://cfrp.e6ex.com/rawgit/triwinds/yuzu-tools/main/keys_info.json')
    return resp.json()


def download_keys_by_name(name):
    keys_info = get_keys_info()
    if name not in keys_info:
        raise RuntimeError(f'No such key [{name}].')
    key_info = keys_info[name]
    url = key_info['url'].replace('https://drive.google.com', 'https://cfrp.e6ex.com/gd')
    logger.info(f'Downloading keys [{name}] from {url}')
    data = requests.get(url)
    file = download_path.joinpath(name)
    with file.open('wb') as f:
        f.write(data.content)
    return file


def check_and_install_msvc():
    windir = Path(os.environ['windir'])
    if windir.joinpath(r'System32\msvcp140_atomic_wait.dll').exists():
        logger.info(f'msvc already installed.')
        return
    from module.downloader import download
    from module.msg_notifier import send_notify
    send_notify('开始下载 msvc 安装包...')
    logger.info('downloading msvc installer...')
    download_info = download('https://aka.ms/vs/17/release/VC_redist.x64.exe')
    install_file = download_info.files[0]
    send_notify('安装 msvc...')
    logger.info('install msvc...')
    process = subprocess.Popen([install_file.path])
    # process.wait()


if __name__ == '__main__':
    # infos = get_firmware_infos()
    # for info in infos:
    #     print(info)
    check_and_install_msvc()
