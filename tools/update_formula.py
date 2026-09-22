#!/usr/bin/env python3
"""Verify a published Omnivox release before updating its Homebrew formula."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


REPOSITORY = "bartbunting/omnivox"
FORMULA = Path(__file__).resolve().parents[1] / "Formula" / "omnivox.rb"
ARCHITECTURES = ("arm64", "x64")


def version_number(value):
    value = value.removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError("Expected a stable version such as 1.12.0")
    return value


def gh(*arguments):
    return subprocess.check_output(["gh", *arguments], text=True, timeout=180)


def release_hashes(version):
    tag = f"v{version}"
    release = json.loads(gh(
        "release", "view", tag, "--repo", REPOSITORY,
        "--json", "tagName,isDraft,isPrerelease",
    ))
    if release["tagName"] != tag or release["isDraft"] or release["isPrerelease"]:
        raise ValueError("Only the requested published stable release is allowed")

    names = {arch: f"omnivox-{version}-macos-{arch}.tar.gz" for arch in ARCHITECTURES}
    with tempfile.TemporaryDirectory(prefix="omnivox-formula-") as temporary:
        directory = Path(temporary)
        arguments = ["release", "download", tag, "--repo", REPOSITORY,
                     "--dir", temporary, "--pattern", "sha256sums.txt"]
        for name in names.values():
            arguments.extend(["--pattern", name])
        gh(*arguments)
        manifest = (directory / "sha256sums.txt").read_text()
        hashes = {}
        for arch, name in names.items():
            matches = re.findall(
                rf"^([0-9a-fA-F]{{64}}) [ *]{re.escape(name)}$", manifest, re.M,
            )
            if len(matches) != 1:
                raise ValueError(f"Expected exactly one checksum for {name}")
            digest = hashlib.sha256()
            with (directory / name).open("rb") as archive:
                for chunk in iter(lambda: archive.read(1024 * 1024), b""):
                    digest.update(chunk)
            hashes[arch] = digest.hexdigest()
            if hashes[arch] != matches[0].lower():
                raise ValueError(f"Checksum mismatch for {name}")
            print(f"Verified {name}: {hashes[arch]}")
        return hashes


def url_pattern(arch):
    base = re.escape(f"https://github.com/{REPOSITORY}/releases/download/v")
    return rf'{base}(\d+\.\d+\.\d+)/omnivox-(\d+\.\d+\.\d+)-macos-{arch}\.tar\.gz'


def formula_version(original):
    versions = []
    for arch in ARCHITECTURES:
        matches = re.findall(url_pattern(arch), original)
        if len(matches) != 1 or matches[0][0] != matches[0][1]:
            raise ValueError(f"Expected one consistent {arch} release URL")
        versions.append(matches[0][0])
    if len(set(versions)) != 1:
        raise ValueError("Mac release URLs have different versions")
    return versions[0]


def render_formula(original, version, hashes):
    current = formula_version(original)
    if tuple(map(int, version.split("."))) < tuple(map(int, current.split("."))):
        raise ValueError(f"Refusing downgrade from {current} to {version}")
    updated = original
    for arch in ARCHITECTURES:
        url = (f"https://github.com/{REPOSITORY}/releases/download/v{version}/"
               f"omnivox-{version}-macos-{arch}.tar.gz")
        updated = re.sub(url_pattern(arch), url, updated)
        pattern = rf'(url "[^"\n]+-macos-{arch}\.tar\.gz"\n\s+sha256 ")([0-9a-f]{{64}})(")'
        matches = list(re.finditer(pattern, updated))
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {arch} formula URL and checksum")
        if current == version and matches[0][2] != hashes[arch]:
            raise ValueError(f"Published {arch} archive changed under version {version}")
        updated = re.sub(pattern, lambda match: match[1] + hashes[arch] + match[3], updated)
    if current != version:
        updated = re.sub(r"^  revision \d+\n", "", updated, flags=re.M)
    return updated


def update_formula(path, version, check=False):
    original = path.read_text()
    updated = render_formula(original, version, release_hashes(version))
    if check:
        if updated != original:
            raise ValueError("Formula does not match the requested release")
        print("Formula matches both verified release archives")
    elif updated == original:
        print("Formula is already current")
    else:
        path.write_text(updated)
        print(f"Updated {path}; review the diff and run the Mac checks before merging")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", nargs="?", help="Published stable version, with or without v")
    parser.add_argument("--check", action="store_true", help="Verify without editing")
    arguments = parser.parse_args()
    try:
        if arguments.version is None and not arguments.check:
            raise ValueError("Specify a published version to update, or use --check")
        version = version_number(arguments.version) if arguments.version else formula_version(FORMULA.read_text())
        update_formula(FORMULA, version, arguments.check)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
