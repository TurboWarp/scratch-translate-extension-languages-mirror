# Below is the license for this script itself.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.

import os
import io
import json
import subprocess
import urllib.request
import tarfile
import shutil
from collections import OrderedDict

def get_git_commit_summaries():
    result = subprocess.run([
        'git',
        'log',
        '--pretty=format:%s'
    ], capture_output=True, text=True, check=True)
    return result.stdout.split('\n')

def create_git_commit(message, date):
    print(f'Creating commit: {message}')
    subprocess.run(['git', 'stage', 'package'], check=True)
    subprocess.run([
        'git',
        'commit',
        '-m',
        message,
        '-m',
        f'Released on {date}',
        '--author="scratch-translate-extension-languages-mirror bot <scratch-translate-extension-languages-mirror@turbowarp.org>"',
        '--date',
        date
    ], check=True)

def get_registry_data():
    with urllib.request.urlopen('https://registry.npmjs.org/scratch-translate-extension-languages') as registry:
        return json.load(registry)

def unpack_tarball(url):
    print(f'Downloading {url}')
    shutil.rmtree('package', ignore_errors=True)
    with urllib.request.urlopen(url) as remote_file:
        data = io.BytesIO(remote_file.read())
    with tarfile.open(fileobj=data, mode='r') as tar:
        # there will always be an inner `package` folder
        tar.extractall()

def pretty_print_json(json_str):
    try:
        parsed = json.loads(json_str)
        # ensure_ascii because there's a lot of non-ascii characters we don't want to rewrite as \u1234
        # sort_keys because upstream's JSON is in random order
        return json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=True)
    except json.JSONDecodeError as e:
        return json_str

def cleanup_package():
    with open('package/languages.json', 'r') as f:
        pretty = pretty_print_json(f.read())
    with open('package/languages.json', 'w') as f:
        f.write(pretty)

if __name__ == '__main__':
    commits = get_git_commit_summaries()
    registry_data = get_registry_data()

    # The versions we get from npm are in order of publish date, which is what we want
    # The order is a bit messy but note that we **don't** want semver order.
    for version, version_data in registry_data['versions'].items():
        if version in commits:
            print(f'Already have {version}')
            continue

        unpack_tarball(version_data['dist']['tarball'])
        cleanup_package()
        create_git_commit(version, registry_data['time'][version])
