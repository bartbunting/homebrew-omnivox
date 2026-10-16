class Omnivox < Formula
  desc "Cross-platform Emacsvox and Emacspeak speech server"
  homepage "https://github.com/bartbunting/omnivox"
  license all_of: ["GPL-3.0-or-later", "GPL-2.0-or-later"]

  depends_on :macos

  on_macos do
    on_arm do
      url "https://github.com/bartbunting/omnivox/releases/download/v1.18.0/omnivox-1.18.0-macos-arm64.tar.gz"
      sha256 "fb110d30ccf56c6e6aefe00af5a14566afe94f33d6123a325bf0002d475171a0"
    end
    on_intel do
      url "https://github.com/bartbunting/omnivox/releases/download/v1.18.0/omnivox-1.18.0-macos-x64.tar.gz"
      sha256 "24d8058abfd26725623a8c400ff737d5ff7e5c0bfded75f82f08fb5da512781a"
    end
  end

  def install
    libexec.install Dir["*"]
    bin.write_exec_script libexec/"omnivox"
  end

  def caveats
    <<~EOS
      The upstream Emacspeak adapter is installed at:
        #{opt_libexec}/omnivox-voices.el

      Emacsvox uses its own bundled adapter. Configure it to use:
        #{opt_bin}/omnivox

      TGSpeechBox and its voice profiles are included.
      Other optional engine companions and voice models are installed separately.
      Keep user-managed files outside Homebrew's Cellar so upgrades preserve them.
      Restart your speech server after upgrading to use the new version.

      The release binaries are not code-signed with an Apple Developer ID or
      notarized, so macOS Gatekeeper may warn.
    EOS
  end

  test do
    assert_equal "omnivox #{version}", shell_output("#{bin}/omnivox --version").strip
    assert_match "[espeak:", shell_output("#{bin}/omnivox --engine espeak --list-voices")

    assert_path_exists libexec/"tgspeechbox/omnivox-tgspeechbox-helper"

    %w[espeak native tgspeechbox].each do |engine|
      output = testpath/"#{engine}.wav"
      system bin/"omnivox", "--engine", engine, "--dump-wav", "", output,
             "Homebrew speech synthesis verification."
      assert_path_exists output
      assert_equal "RIFF", output.binread(4)
      assert_operator output.size, :>, 44
    end
  end
end
