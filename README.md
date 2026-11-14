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
Emacspeak adapter, the RHVoice integration helper, TGSpeechBox with its voice
profiles and language data, and the release's notices. Apple system speech,
eSpeak and TGSpeechBox are available without installing separate companions.
RHVoice still needs a separately installed compatible runtime and voice data;
including its helper does not establish macOS runtime support. Piper, Flite,
RuTTS, and user voice models are not installed by this formula.

The binaries are taken directly from a published Omnivox release and
verified against SHA-256 hashes. Homebrew does not compile Rust or create
additional binary releases for this tap. The upstream binaries are not signed
with an Apple Developer ID or notarized; consult the upstream
[deployment guide](https://github.com/bartbunting/omnivox/blob/main/.github/DEPLOYMENT.md)
if macOS blocks execution.

## Opt-in testing prerelease

`omnivox-pre` is a separate keg-only formula. It can coexist with stable
`omnivox` and does not replace the ordinary `omnivox` command:

```sh
brew install bartbunting/omnivox/omnivox-pre
"$(brew --prefix omnivox-pre)/bin/omnivox" --version
export OMNIVOX_PROGRAM="$(brew --prefix omnivox-pre)/bin/omnivox"
```

Use this explicit executable in your testing Emacs session; do not force-link
the formula. For device selection, use the paired Emacsvox client and isolated
profile from the release's
[Mac testing guide](https://github.com/bartbunting/omnivox/blob/v1.19.0-pre.2/docs/guides/macos-audio-devices.md).
Physical device switching and audible Mac acceptance remain tester checks.

Upgrade with `brew update` then `brew upgrade omnivox-pre`, and restart the
testing speech session. Remove it with `brew uninstall omnivox-pre`; stable
remains installed. Optional companions and user configuration stay outside the
Cellar as for the stable formula.

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
hashes, and only then updates both release URLs and hashes in the formula. It does
not create an Omnivox release, tag, commit, or push. Replacing a published
archive under the same version is rejected.

Commit the formula change to a branch and open a pull request. After the Mac
checks pass, merge it. Users can then obtain the new version with `brew update`
and `brew upgrade omnivox`. Formula updates are explicit; this repository does
not automatically publish future versions or need cross-repository secrets.

Parham contributed the original formula. Contributions through pull requests
are welcome; repository ownership is not required.

### Maintaining the prerelease formula

Use the explicit prerelease path after the numbered GitHub prerelease is public:

```sh
python3 tools/update_formula.py 1.19.0-pre.2 --prerelease
python3 tools/update_formula.py 1.19.0-pre.2 --prerelease --check
```

This updates only `Formula/omnivox-pre.rb`. It requires a published `-pre.N`
release and verifies both archive hashes. Drafts, stable releases, downgrades and
changed same-version archives are rejected. Stable updates continue to reject
prereleases. Require both native Mac checks on the final PR commit, merge, then
rerun the explicit version check on merged `main`. Record the PR, commit and
checks in the upstream release report.

## Checks

```sh
python3 -m unittest discover -s tests -v
python3 tools/update_formula.py --check
brew audit --formula bartbunting/omnivox/omnivox
brew test bartbunting/omnivox/omnivox
```

The `--check` command uses the formula's current version and verifies the
published downloads without editing it. CI runs on native Apple
Silicon and Intel Macs. It checks formula style and audit, installation,
version and voice discovery, WAV synthesis through eSpeak, Apple speech and TGSpeechBox,
reinstallation, a packaging-revision upgrade using the same upstream payload,
and uninstallation for both formulas. It also checks that installing and removing
the keg-only prerelease preserves the stable command. A real upgrade between different Omnivox versions and
audible speech inside Emacs remain separate acceptance checks.

The formula's license declaration describes the installed upstream payload.
Upstream component licenses and notices are preserved in `libexec`; see
[Omnivox licensing](https://github.com/bartbunting/omnivox/blob/main/docs/LICENSING.md).
