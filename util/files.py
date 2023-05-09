import json
import os
import re
import subprocess
from urllib.request import urlretrieve

from util.helper import clear_console, is_windows_machine, http_request

PACKAGE_LOCK_FILE = "package-lock.json"
PACKAGE_JSON_FILE = "package.json"
INPUT_FOLDER = "./input/"
OUTPUT_FOLDER = "./output/"


def make_input_output_folders():
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


def has_file(folder, filename):
    return os.path.isfile(os.path.join(folder, filename))


def has_package_lock():
    return has_file(INPUT_FOLDER, PACKAGE_LOCK_FILE)


def has_package_json():
    return has_file(INPUT_FOLDER, PACKAGE_JSON_FILE)


def package_lock_parse():
    # open the package_lock.json.
    with open(os.path.join(INPUT_FOLDER, PACKAGE_LOCK_FILE)) as package_lock:
        package_lock_data = json.load(package_lock)

    if is_windows_machine():
        dependencies = package_lock_data["dependencies"]
    else:
        dependencies = package_lock_data["packages"]

    for index, package_name in enumerate(dependencies):
        if package_name == "":
            continue

        clear_console()

        print(f"Files downloaded: {str(index)}/{str(len(dependencies))}")

        package = dependencies[package_name]

        resolved = package["resolved"]
        file_name = resolved.split("/")[-1]

        retrieve_to_output(resolved, file_name)


def package_json_parse():
    subprocess.run(["npm", "i", "--package-lock-only"], cwd=INPUT_FOLDER, shell=True)


def download_npm_package(package):
    subprocess.run(["npm", "init", "-y"], cwd=INPUT_FOLDER, shell=True)
    subprocess.run(["npm", "i", package, "--package-lock-only"], cwd=INPUT_FOLDER, shell=True)
    if has_package_json():
        os.remove(os.path.join(INPUT_FOLDER, PACKAGE_JSON_FILE))


def go_to_output():
    if is_windows_machine():
        subprocess.run(["Explorer", "."], cwd=OUTPUT_FOLDER, shell=True)
    else:
        subprocess.run(["xdg-open", OUTPUT_FOLDER], shell=True)


def retrieve_to_output(url, filename):
    urlretrieve(url, os.path.join(OUTPUT_FOLDER, filename))


def find_distribution(response_body, version):
    all_version_info = response_body["releases"][version]

    # In case Source Distribution Exists
    search_value = "sdist"

    for version_info in all_version_info:
        if search_value in version_info["packagetype"]:
            return version_info

    # TODO Add built distributions selection menu for the following operating systems (In case it exists) :
    #  Windows64,Windows32,MacOS,Linux X86-64, Linux i686

def download_package_dependencies(package_name):
    import pkg_resources, sys

    python_version = f'{sys.version_info.major}.{sys.version_info.minor}'

    dist = pkg_resources.get_distribution(package_name)

    for dependency in dist.requires():
        dependency = dependency.unsafe_name
        if ';' in dependency:
            dependency = dependency[0: dependency.find(';')]
      
        subprocess.run(f'py -{python_version} -m pip download --no-binary=:all: --no-deps -d ./output {dependency}')
        if dependency == 'numpy':
            subprocess.run(f'py -{python_version} -m pip download --no-binary=:all: --no-deps --no-build-isolation -d ./output {dependency}')
        download_package_dependencies(dependency)




def download_pip_package(package):
    url = f"https://pypi.org/pypi/{package}/json"

    response_body = http_request(url)
    if not response_body:
        return

    version = response_body["info"]["version"]

    version_info = find_distribution(response_body, version)
    download_link = version_info["url"]
    download_name = version_info["filename"]

    retrieve_to_output(download_link, download_name)

    download_package_dependencies(package)

    print("Download successful!")
