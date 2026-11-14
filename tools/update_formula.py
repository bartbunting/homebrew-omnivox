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
PRERELEASE_FORMULA = FORMULA.with_name("omnivox-pre.rb")
NUMBER = r"(?:0|[1-9][0-9]*)"
STABLE = rf"{NUMBER}\.{NUMBER}\.{NUMBER}"
PRERELEASE = rf"{STABLE}-pre\.[1-9][0-9]*"
ARCHITECTURES = ("arm64", "x64")


def version_number(value, prerelease=False):
    value = value.removeprefix("v")
    if not re.fullmatch(PRERELEASE if prerelease else STABLE, value):
        channel = "numbered prerelease (1.19.0-pre.1)" if prerelease else "stable version (1.19.0)"
        raise ValueError(f"Expected a {channel}")
    return value


def version_key(value):
    base, _, pre = value.partition("-pre.")
    return (*map(int, base.split(".")), 0 if pre else 1, int(pre or 0))


def gh(*arguments):
    return subprocess.check_output(["gh", *arguments], text=True, timeout=180)


def release_hashes(version, prerelease=False):
    version_number(version, prerelease)
    tag = f"v{version}"
    release = json.loads(gh(
        "release", "view", tag, "--repo", REPOSITORY,
        "--json", "tagName,isDraft,isPrerelease",
    ))
    if release["tagName"] != tag or release["isDraft"] or release["isPrerelease"] != prerelease:
        raise ValueError("Only the requested published release with matching channel is allowed")

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
    version = rf"{STABLE}(?:-pre\.[1-9][0-9]*)?"
    return rf'{base}({version})/omnivox-({version})-macos-{arch}\.tar\.gz'


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


def render_formula(original, version, hashes, prerelease=False):
    version_number(version, prerelease)
    current = formula_version(original)
    if ("-pre." in current) != prerelease:
        raise ValueError("Formula channel does not match requested release")
    if prerelease and re.findall(r'^  version "([^"\n]+)"$', original, re.M) != [current]:
        raise ValueError("Explicit formula version does not match the archive URLs")
    if version_key(version) < version_key(current):
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
    if prerelease:
        updated, count = re.subn(r'^  version "[^"\n]+"$', f'  version "{version}"', updated, flags=re.M)
        if count != 1:
            raise ValueError("Expected one explicit prerelease formula version")
    return updated


def update_formula(path, version, check=False, prerelease=False):
    original = path.read_text()
    updated = render_formula(original, version, release_hashes(version, prerelease), prerelease)
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
    parser.add_argument("version", nargs="?", help="Published version, with or without v; stable unless --prerelease")
    parser.add_argument("--prerelease", action="store_true", help="Select the separate keg-only omnivox-pre formula")
    parser.add_argument("--check", action="store_true", help="Verify without editing")
    arguments = parser.parse_args()
    try:
        if arguments.version is None and not arguments.check:
            raise ValueError("Specify a published version to update, or use --check")
        formula = PRERELEASE_FORMULA if arguments.prerelease else FORMULA
        requested = arguments.version or formula_version(formula.read_text())
        version = version_number(requested, arguments.prerelease)
        update_formula(formula, version, arguments.check, arguments.prerelease)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
