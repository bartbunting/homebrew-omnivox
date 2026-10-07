class Omnivox < Formula
  desc "Cross-platform Emacsvox and Emacspeak speech server"
  homepage "https://github.com/bartbunting/omnivox"
  license all_of: ["GPL-3.0-or-later", "GPL-2.0-or-later"]

  depends_on :macos

  on_macos do
    on_arm do
      url "https://github.com/bartbunting/omnivox/releases/download/v1.16.1/omnivox-1.16.1-macos-arm64.tar.gz"
      sha256 "424d52aa84ac2f2b4152f75dbf1f015c612bc72823126132ae1320b4b95bee91"
    end
    on_intel do
      url "https://github.com/bartbunting/omnivox/releases/download/v1.16.1/omnivox-1.16.1-macos-x64.tar.gz"
      sha256 "06c59086bdd12d933e35b27db9ce3edae924091eb0e81e08e3b94f3877185167"
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

      Optional engine companions and voice models are installed separately.
      Keep user-managed files outside Homebrew's Cellar so upgrades preserve them.
      Restart your speech server after upgrading to use the new version.

      The release binaries are not code-signed with an Apple Developer ID or
      notarized, so macOS Gatekeeper may warn.
    EOS
  end

  test do
    assert_equal "omnivox #{version}", shell_output("#{bin}/omnivox --version").strip
    assert_match "[espeak:", shell_output("#{bin}/omnivox --engine espeak --list-voices")

    %w[espeak native].each do |engine|
      output = testpath/"#{engine}.wav"
      system bin/"omnivox", "--engine", engine, "--dump-wav", "", output,
             "Homebrew speech synthesis verification."
      assert_path_exists output
      assert_equal "RIFF", output.binread(4)
      assert_operator output.size, :>, 44
    end
  end
end
