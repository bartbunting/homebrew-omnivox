# Omnivox for Homebrew

Install the [Omnivox speech server](https://github.com/bartbunting/omnivox)
on macOS, using its published Apple Silicon or Intel binary archive.

## Install and upgrade

With [Homebrew](https://brew.sh) installed:

```sh
brew install bartbunting/omnivox/omnivox
omnivox --version
```

To upgrade:

```sh
brew update
brew upgrade omnivox
```

Restart your speech server after upgrading. An already running process keeps
using the old executable. To remove the Homebrew installation:

```sh
brew uninstall omnivox
```

The formula installs the main server, its matching eSpeak NG data, the upstream
Emacspeak adapter, the RHVoice integration helper, and the release's notices.
Apple system speech and eSpeak are available without optional companions.
RHVoice still needs a separately installed compatible runtime and voice data;
including its helper does not establish macOS runtime support. Piper, Flite,
RuTTS, and user voice models are not installed by this formula.

The binaries are taken directly from an existing stable Omnivox release and
verified against SHA-256 hashes. Homebrew does not compile Rust or create
additional binary releases for this tap. The upstream binaries are not signed
with an Apple Developer ID or notarized; consult the upstream
[deployment guide](https://github.com/bartbunting/omnivox/blob/main/.github/DEPLOYMENT.md)
if macOS blocks execution.

## Emacs integration

Find the stable executable path with:

```sh
echo "$(brew --prefix omnivox)/bin/omnivox"
```

Use that path in your existing speech-server configuration. Emacs launched from
Finder may not inherit your shell's Homebrew PATH. If a manually installed copy
already exists, check `command -v omnivox` and your Emacs configuration to ensure
they select the intended installation.

Emacsvox uses its own bundled adapter. For Emacspeak, the supplied adapter is at:

```sh
echo "$(brew --prefix omnivox)/libexec/omnivox-voices.el"
```

These paths follow Homebrew's current-version symlink. Avoid hard-coding a
versioned `Cellar/omnivox/...` directory. Keep optional companions, downloaded
voices, and configuration outside the Cellar and configure their explicit
paths using the upstream engine guides; Homebrew may remove old kegs on upgrade.

## Maintaining a release

After an Omnivox stable release has been published and passed its own gates:

```sh
git clone https://github.com/bartbunting/homebrew-omnivox.git
cd homebrew-omnivox
python3 tools/update_formula.py VERSION
git diff -- Formula/omnivox.rb
```

The updater requires Python 3.9 or newer and an authenticated
[GitHub CLI](https://cli.github.com). Replace `VERSION` with the published
version, for example `1.12.0`. It rejects drafts, prereleases, and downgrades,
downloads both Mac archives and their checksum manifest, verifies both archive
hashes, and only then updates the version and hashes in the formula. It does
not create an Omnivox release, tag, commit, or push. Replacing a published
archive under the same version is rejected.

Commit the formula change to a branch and open a pull request. After the Mac
checks pass, merge it. Users can then obtain the new version with `brew update`
and `brew upgrade omnivox`. Formula updates are explicit; this repository does
not automatically publish future versions or need cross-repository secrets.

Parham contributed the original formula. Contributions through pull requests
are welcome; repository ownership is not required.

## Checks

```sh
python3 -m unittest discover -s tests -v
python3 tools/update_formula.py 1.12.0 --check
brew audit --formula bartbunting/omnivox/omnivox
brew test bartbunting/omnivox/omnivox
```

Use the formula's current version for `--check`; it verifies the published
downloads against the formula without editing it. CI runs on native Apple
Silicon and Intel Macs. It checks formula style and audit, installation,
version and voice discovery, WAV synthesis through eSpeak and Apple speech,
reinstallation, a packaging-revision upgrade using the same upstream payload,
and uninstallation. A real upgrade between different Omnivox versions and
audible speech inside Emacs remain separate acceptance checks.

The formula's license declaration describes the installed upstream payload.
Upstream component licenses and notices are preserved in `libexec`; see
[Omnivox licensing](https://github.com/bartbunting/omnivox/blob/main/docs/LICENSING.md).
