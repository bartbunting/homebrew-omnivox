class Omnivox < Formula
  desc "Cross-platform Emacsvox and Emacspeak speech server"
  homepage "https://github.com/bartbunting/omnivox"
  license all_of: ["GPL-3.0-or-later", "GPL-2.0-or-later"]

  depends_on :macos

  on_macos do
    on_arm do
      url "https://github.com/bartbunting/omnivox/releases/download/v1.17.0/omnivox-1.17.0-macos-arm64.tar.gz"
      sha256 "65c23f7464ba292c15ef786401279548bffc2c00990e9cc487e2d21272410730"
    end
    on_intel do
      url "https://github.com/bartbunting/omnivox/releases/download/v1.17.0/omnivox-1.17.0-macos-x64.tar.gz"
      sha256 "f2cd3072d9e13dd451803a01f7cf391dc4e234a6b3473f4743458350af294de3"
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
