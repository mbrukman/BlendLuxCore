#!/usr/bin/env python3

import argparse
import os
from urllib import request
import subprocess
import shutil
import tarfile
import zipfile

script_dir = os.path.dirname(os.path.realpath(__file__))

# These are the same as in BlendLuxCore/bin/get_binaries.py
linux_binaries = ["libembree.so.2", "libtbb.so.2", "pyluxcore.so", "luxcoreui"]
windows_binaries = ["embree.dll", "tbb.dll", "OpenImageIO.dll", "pyluxcore.pyd", "luxcoreui.exe"]


def print_divider():
    print("=" * 60)


def build_name(prefix, version_string, suffix):
    return prefix + version_string + suffix


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version_string",
                        help='E.g. "v2.0alpha1" or "v2.0". Used to download the LuxCore zips')
    args = parser.parse_args()

    # Archives we need.
    # Note: for linux versions, we need the SDK version
    # because pyluxcore.so is missing from the normal version
    url_prefix = "https://github.com/LuxCoreRender/LuxCore/releases/download/luxcorerender_"
    prefix = "luxcorerender-"
    suffixes = [
        "-linux64-sdk.tar.bz2",
        "-linux64-opencl-sdk.tar.bz2",
        "-win64.zip",
        "-win64-opencl.zip",
    ]

    # Download LuxCore binaries for all platformsprint()
    print_divider()
    print("Downloading LuxCore releases")
    print_divider()

    for suffix in suffixes:
        name = build_name(prefix, args.version_string, suffix)

        # Check if file already downloaded
        if name not in os.listdir(script_dir):
            destination = os.path.join(script_dir, name)
            url = url_prefix + args.version_string + "/" + name
            print('Downloading: "%s"' % url)
            request.urlretrieve(url, destination)
        else:
            print('File already downloaded: "%s"' % name)

    print_divider()
    print("Cloning BlendLuxCore")
    print_divider()

    # Clone BlendLuxCore (will later put the binaries in there)
    clone_args = ["git", "clone", "https://github.com/LuxCoreRender/BlendLuxCore.git"]
    git_process = subprocess.Popen(clone_args)
    git_process.wait()
    repo_path = os.path.join(script_dir, "BlendLuxCore")

    print_divider()
    print("Creating BlendLuxCore release subdirectories")
    print_divider()

    # Create subdirectories for all platforms
    for suffix in suffixes:
        name = "BlendLuxCore" + suffix.split(".")[0]
        destination = os.path.join(script_dir, name, "BlendLuxCore")

        if os.path.exists(destination):
            print('Destination already exists, deleting it: "%s"' % destination)
            shutil.rmtree(destination)

        shutil.copytree(repo_path, destination)


    # Linux archives are tar.bz2
    linux_suffixes = [suffix for suffix in suffixes if suffix.startswith("-linux")]
    for suffix in linux_suffixes:
        dst_name = "BlendLuxCore" + suffix.split(".")[0]
        destination = os.path.join(script_dir, dst_name, "BlendLuxCore", "bin")

        print()
        print_divider()
        print("Extracting tar to", dst_name)
        print_divider()

        # have to use a temp dir (weird extract behaviour)
        temp_dir = os.path.join(script_dir, "temp")
        # Make sure we don't delete someone's beloved temp folder later
        while os.path.exists(temp_dir):
            temp_dir += "_"
        os.mkdir(temp_dir)

        tar_name = build_name(prefix, args.version_string, suffix)
        print("Reading tar file:", tar_name)
        print("(This will take a while)")

        with tarfile.open(tar_name, "r:bz2") as tar:
            for member in tar.getmembers():
                basename = os.path.basename(member.name)
                if basename not in linux_binaries:
                    continue

                # have to use a temp dir (weird extract behaviour)
                print('Extracting "%s" to "%s"' % (basename, temp_dir))
                tar.extract(member, path=temp_dir)
                src = os.path.join(temp_dir, member.name)

                # move to real target directory
                dst = os.path.join(destination, basename)
                print('Moving "%s" to "%s"' % (src, dst))
                if not os.path.isfile(dst):
                    shutil.move(src, dst)

        shutil.rmtree(temp_dir)

    # Windows archives are zip
    windows_suffixes = [suffix for suffix in suffixes if suffix.startswith("-win")]
    for suffix in windows_suffixes:
        dst_name = "BlendLuxCore" + suffix.split(".")[0]
        destination = os.path.join(script_dir, dst_name, "BlendLuxCore", "bin")

        print()
        print_divider()
        print("Extracting zip to", dst_name)
        print_divider()

        # have to use a temp dir (weird extract behaviour)
        temp_dir = os.path.join(script_dir, "temp")
        # Make sure we don't delete someone's beloved temp folder later
        while os.path.exists(temp_dir):
            temp_dir += "_"
        os.mkdir(temp_dir)

        zip_name = build_name(prefix, args.version_string, suffix)
        print("Reading zip file:", zip_name)

        with zipfile.ZipFile(zip_name, "r") as zip:
            for member in zip.namelist():
                basename = os.path.basename(member)  # in zip case, member is just a string
                if basename not in windows_binaries:
                    continue

                # have to use a temp dir (weird extract behaviour)
                print('Extracting "%s" to "%s"' % (basename, temp_dir))
                src = zip.extract(member, path=temp_dir)

                # move to real target directory
                dst = os.path.join(destination, basename)
                print('Moving "%s" to "%s"' % (src, dst))
                shutil.move(src, dst)

        shutil.rmtree(temp_dir)

    # Package everything
    print()
    print_divider()
    print("Packaging BlendLuxCore releases")
    print_divider()

    release_dir = os.path.join(script_dir, "release-" + args.version_string)
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.mkdir(release_dir)

    for suffix in suffixes:
        name = "BlendLuxCore" + suffix.split(".")[0]
        zip_this = os.path.join(script_dir, name)
        print("Zipping:", name)
        zip_name = name + ".zip"

        shutil.make_archive(name, 'zip', zip_this)

        shutil.move(zip_this + ".zip", os.path.join(release_dir, zip_name))

    print()
    print_divider()
    print("Results can be found in: release-" + args.version_string)
    print_divider()


if __name__ == "__main__":
    main()