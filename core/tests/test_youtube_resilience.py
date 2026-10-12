"""Anti-error YouTube: auto-pindah keluarga IP (IPv4/IPv6) + lapis caption cadangan.

Seri ini mengunci dua hal yang dulu membuat video YouTube gagal/gagal lama:
1. yt-dlp dikunci pada keluarga alamat default; bila keluarga itu diblokir
   tantangan bot, SEMUA jalur (metadata, caption, unduh) ikut mati.
2. Caption hanya punya satu jalur; bila gagal, analisis jatuh ke Whisper
   (menit) — itu sebabnya satu video bisa >2 menit.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from studiozai.pipeline import captions, download, ytnet


@pytest.fixture(autouse=True)
def reset_family():
    """Tiap tes mulai dari keluarga IPv4 lalu dipulihkan setelahnya."""
    original = ytnet._preferred_first
    ytnet._preferred_first = ytnet.FAMILY_IPV4
    yield
    ytnet._preferred_first = original


# --------------------------------------------------------------------- ytnet


def test_urutan_keluarga_kembali_ke_pemenang():
    assert ytnet.get_family_order() == ["ipv4", "system"]
    ytnet.mark_family_working("system")
    assert ytnet.get_family_order() == ["system", "ipv4"]
    ytnet.mark_family_working("ipv4")
    assert ytnet.get_family_order() == ["ipv4", "system"]
    # Nilai di luar keluarga sah diabaikan (tidak merusak urutan).
    ytnet.mark_family_working("tor")
    assert ytnet.get_family_order() == ["ipv4", "system"]


def test_deteksi_error_bergantung_jaringan():
    assert ytnet.is_family_retryable(RuntimeError("Sign in to confirm you're not a bot"))
    assert ytnet.is_family_retryable(Exception("RequestBlocked"))
    assert ytnet.is_family_retryable(Exception("HTTP Error 503: unavailable"))
    assert ytnet.is_family_retryable(RuntimeError("Connection reset by peer"))
    # Bukan masalah IP -> tidak layak mengulang di keluarga lain.
    assert not ytnet.is_family_retryable(RuntimeError("Video unavailable"))
    assert not ytnet.is_family_retryable(ValueError("bukan URL yang valid"))


def test_try_families_gagal_lalu_berhasil_di_keluarga_berikut():
    tried: list[str] = []

    def attempt(family: str) -> str:
        tried.append(family)
        if family == "ipv4":
            raise RuntimeError("Sign in to confirm you're not a bot")
        return "hasil"

    result, winner = ytnet.try_families(attempt)
    assert result == "hasil"
    assert winner == "system"
    assert tried == ["ipv4", "system"]
    # Pemenang dicatat: panggilan berikutnya langsung mulai dari dia.
    assert ytnet.get_family_order()[0] == "system"


def test_try_families_error_non_jaringan_langsung_melempar():
    tried: list[str] = []

    def attempt(family: str) -> str:
        tried.append(family)
        raise RuntimeError("Video unavailable. This video is not available")

    with pytest.raises(RuntimeError, match="Video unavailable"):
        ytnet.try_families(attempt)
    assert tried == ["ipv4"], "tidak boleh membuang waktu di keluarga kedua"


def test_try_families_semua_gagal_menggabungkan_riwayat():
    def attempt(family: str) -> str:
        raise RuntimeError("Sign in to confirm you're not a bot")

    with pytest.raises(RuntimeError) as exc:
        ytnet.try_families(attempt)
    assert "ipv4" in str(exc.value) and "system" in str(exc.value)


def test_family_options_dan_opener_tertambat():
    assert ytnet.family_options("ipv4") == {"source_address": "0.0.0.0"}
    assert ytnet.family_options("system") == {}
    # Opener urllib ikut menambatkan alamat sumber bila keluarga ipv4.
    assert ytnet.opener_for("ipv4") is ytnet.opener_for("ipv4"), "opener harus di-cache"
    assert ytnet.opener_for("ipv4") is not ytnet.opener_for("system")


def test_friendly_error_menyembunyikan_dinding_teks():
    raw = "Sign in to confirm you're not a bot. See https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how"
    message = ytnet.friendly_error("membaca link", RuntimeError(raw))
    assert "verifikasi jaringan" in message
    assert "cookies" in message
    assert "github.com" not in message, "URL FAQ yt-dlp tidak boleh bocor ke UI"


# ----------------------------------------------------------------- fetch_info


def test_fetch_info_pindah_keluarga_otomatis(monkeypatch):
    seen: list[object] = []

    class FakeYDL:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=False):
            seen.append(self.options.get("source_address"))
            if self.options.get("source_address") != "0.0.0.0":
                raise RuntimeError("Sign in to confirm you're not a bot")
            return {"title": "uji", "duration": 42.0, "formats": []}

    monkeypatch.setattr(download, "_yt_dlp", lambda: SimpleNamespace(YoutubeDL=FakeYDL))
    ytnet.mark_family_working("system")  # mulai dari keluarga yang diblokir

    info = download.fetch_info("https://youtu.be/abc12345678")

    assert info["family"] == "ipv4"
    assert seen == [None, "0.0.0.0"], "harus mencoba keluarga default lalu IPv4"
    assert ytnet.get_family_order()[0] == "ipv4", "IPv4 yang berhasil harus diprioritaskan"


def test_fetch_info_gagal_total_memberi_pesan_ramah(monkeypatch):
    class FakeYDL:
        def __init__(self, options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download=False):
            raise RuntimeError("Sign in to confirm you're not a bot. Use --cookies")

    monkeypatch.setattr(download, "_yt_dlp", lambda: SimpleNamespace(YoutubeDL=FakeYDL))

    with pytest.raises(RuntimeError) as exc:
        download.fetch_info("https://youtu.be/abc12345678")

    message = str(exc.value)
    assert "verifikasi jaringan" in message
    assert "Pengaturan" in message  # solusi konkret ke pengguna
    assert "--cookies" not in message, "instruksi mentah yt-dlp tidak boleh tampil"


# ------------------------------------------------------------------- captions


def _ytdlp_fail(family: str) -> None:
    raise RuntimeError("caption tidak tersedia: Sign in to confirm you're not a bot")


def test_fetch_captions_coba_ytdlp_lalu_jatuh_ke_api(tmp_path, monkeypatch):
    seen: list[str] = []

    def fake_ytdlp(url, out_dir, lang, cookies, progress_cb, family):
        seen.append(f"ytdlp/{family}")
        raise captions._CaptionUnavailable("video ini tidak memiliki caption")

    def fake_api(url, lang, progress_cb, family):
        seen.append(f"api/{family}")
        return {
            "language": "id",
            "source": "youtube",
            "segments": [{"start": 0.0, "end": 1.0, "text": "halo", "words": []}],
            "text": "halo",
        }

    monkeypatch.setattr(captions, "_fetch_via_ytdlp", fake_ytdlp)
    monkeypatch.setattr(captions, "_fetch_via_api", fake_api)

    result = captions.fetch_captions("https://youtu.be/abc12345678", tmp_path, lang="id")

    assert result["segments"][0]["text"] == "halo"
    # yt-dlp dicoba di dua keluarga, API jadi cadangan di keluarga pertama.
    assert seen == ["ytdlp/ipv4", "ytdlp/system", "api/ipv4"]


def test_fetch_captions_blokir_ip_mencoba_keluarga_berikut(tmp_path, monkeypatch):
    seen: list[str] = []

    def fake_ytdlp(url, out_dir, lang, cookies, progress_cb, family):
        seen.append(family)
        if family == "ipv4":
            _ytdlp_fail(family)
        return {
            "language": "id",
            "source": "youtube",
            "segments": [{"start": 0.0, "end": 1.0, "text": "aman", "words": []}],
            "text": "aman",
        }

    monkeypatch.setattr(captions, "_fetch_via_ytdlp", fake_ytdlp)
    monkeypatch.setattr(
        captions, "_fetch_via_api",
        lambda *a: pytest.fail("API tidak perlu dipakai bila keluarga kedua berhasil"),
    )

    result = captions.fetch_captions("https://youtu.be/abc12345678", tmp_path)

    assert result["segments"][0]["text"] == "aman"
    assert seen == ["ipv4", "system"]


def test_fetch_captions_semua_lapis_gagal_memberi_pesan_ramah(tmp_path, monkeypatch):
    monkeypatch.setattr(captions, "_fetch_via_ytdlp", lambda *a: _ytdlp_fail("x"))
    monkeypatch.setattr(
        captions, "_fetch_via_api",
        lambda *a: (_ for _ in ()).throw(RuntimeError("RequestBlocked")),
    )

    with pytest.raises(RuntimeError) as exc:
        captions.fetch_captions("https://youtu.be/abc12345678", tmp_path)

    message = str(exc.value)
    assert "verifikasi jaringan" in message
    assert "youtube-transcript-api" in message or "cookies" in message


def test_video_id_dari_berbagai_bentuk_url():
    assert captions.video_id_of("https://youtu.be/oPZY7nKtUTc") == "oPZY7nKtUTc"
    assert captions.video_id_of("https://www.youtube.com/watch?v=oPZY7nKtUTc&t=10") == "oPZY7nKtUTc"
    assert captions.video_id_of("https://www.youtube.com/shorts/oPZY7nKtUTc") == "oPZY7nKtUTc"
    assert captions.video_id_of("https://www.youtube.com/embed/oPZY7nKtUTc") == "oPZY7nKtUTc"
    assert captions.video_id_of("bukan-url") == ""


# ----------------------------------------------------------------- unduh CDN


def test_http_open_ditambat_ke_keluarga(monkeypatch):
    """Unduhan byte harus memakai opener keluarga, bukan opener bawaan."""
    opened: list[str] = []

    class FakeResponse:
        status = 206
        @property
        def headers(self):
            return {"Content-Range": "bytes 0-1/9"}

        def read(self) -> bytes:
            return b"xx"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class FakeOpener:
        def open(self, request, timeout=None):
            opened.append(request.get_header("Range") or "")
            return FakeResponse()

    monkeypatch.setattr(ytnet, "opener_for", lambda family=None: FakeOpener())

    with download._http_open("https://example.com/v", "bytes=0-1", "ipv4") as response:
        assert response.status == 206
    assert opened == ["bytes=0-1"], "range harus diteruskan ke opener ber-tambatan"


def test_unduh_audio_pindah_keluarga_bila_cdn_ditolak(monkeypatch, tmp_path):
    seen: list[str] = []

    def fake_http_download(url, target, progress_cb=None, family=None):
        seen.append(family or "-")
        if family != "ipv4":
            raise RuntimeError("koneksi unduhan gagal berulang kali")
        Path(target).write_bytes(b"ID3audio")
        return 7

    monkeypatch.setattr(download, "_extract", lambda *a, **k: {"title": "uji"})
    monkeypatch.setattr(download, "_pick_audio_format", lambda *a, **k: {"url": "https://cdn/u.m4a", "ext": "m4a"})
    monkeypatch.setattr(download, "_http_download", fake_http_download)
    ytnet.mark_family_working("system")

    result = download.download_audio("https://youtu.be/abc12345678", tmp_path)

    assert seen == ["system", "ipv4"], "keluarga default dicoba dulu, lalu berganti"
    assert result["path"].endswith(".m4a")
    assert ytnet.get_family_order()[0] == "ipv4"


def test_unduh_audio_semua_keluarga_gagal_pesan_ramah(monkeypatch, tmp_path):
    monkeypatch.setattr(download, "_download_audio_native", lambda *a: (_ for _ in ()).throw(RuntimeError("koneksi cadangan gagal")))
    monkeypatch.setattr(download, "_extract", lambda *a, **k: {"title": "uji"})
    monkeypatch.setattr(download, "_pick_audio_format",
                        lambda *a, **k: {"url": "https://cdn/u.m4a", "ext": "m4a"})
    monkeypatch.setattr(download, "_http_download",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("koneksi unduhan gagal berulang kali")))

    with pytest.raises(RuntimeError) as exc:
        download.download_audio("https://youtu.be/abc12345678", tmp_path)

    message = str(exc.value)
    assert "verifikasi jaringan" in message or "koneksi" in message.lower()


def test_hls_section_menerima_keluarga(monkeypatch, tmp_path):
    """download_range meneruskan keluarga IP ke pengunduh segmen HLS."""
    families: list[str | None] = []

    def fake_section(playlist_url, start, end, out_dir, progress_cb, family=None):
        families.append(family)
        raise RuntimeError("Sign in to confirm you're not a bot")

    monkeypatch.setattr(download, "_hls_section", fake_section)
    monkeypatch.setattr(download, "_extract", lambda *a, **k: {"title": "x"})
    monkeypatch.setattr(download, "_pick_hls_format",
                        lambda *a, **k: {"url": "http://example.com/v.m3u8"})

    with pytest.raises(RuntimeError):
        download.download_range("https://www.youtube.com/watch?v=abcdefghijk", 0, 4,
                                tmp_path / "out")

    assert families == ["ipv4", "system"], "harus mencoba keluarga lain"


# --------------------------------------------------------------------- parser


def test_parser_membuang_ulangan_rolling_window(tmp_path):
    """Caption otomatis YouTube mengulang baris window sebelumnya — harus dibuang."""
    vtt = tmp_path / "a.id.vtt"
    vtt.write_text(
        "WEBVTT\nKind: captions\n\n"
        "00:00:00.040 --> 00:00:02.030 align:start position:0%\n"
        "Halo,<00:00:00.320><c> Guys.</c><00:00:00.640><c> David</c>\n\n"
        "00:00:02.030 --> 00:00:02.040 align:start position:0%\n"
        "Halo, Guys. David\n \n\n"
        "00:00:02.040 --> 00:00:06.789 align:start position:0%\n"
        "Halo, Guys. David\n"
        "kedatangan<00:00:02.679><c> HP</c><00:00:03.159><c> seru</c>\n\n"
        "00:00:06.789 --> 00:00:06.799 align:start position:0%\n"
        "kedatangan HP seru\n",
        encoding="utf-8",
    )

    segments = captions.parse_subtitle_file(vtt)

    assert [segment["text"] for segment in segments] == [
        "Halo, Guys. David",
        "kedatangan HP seru",
    ]
    # Timing kata dihitung dari baris yang tersisa (bukan campuran dua baris).
    assert [word["word"] for word in segments[1]["words"]] == ["kedatangan", "HP", "seru"]
    assert segments[1]["words"][0]["start"] == 2.04
    assert segments[1]["words"][1]["start"] == 2.679


def test_parser_mempertahankan_ucapan_berulang_yang_asli(tmp_path):
    """Pengulangan di tengah kalimat baru TIDAK boleh dianggap salinan window."""
    srt = tmp_path / "a.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nkalimat pertama\n\n"
        "2\n00:00:02,000 --> 00:00:04,000\nkalimat lain sama sekali\n\n"
        "3\n00:00:04,000 --> 00:00:06,000\nkalimat pertama\n",
        encoding="utf-8",
    )

    segments = captions.parse_subtitle_file(srt)

    assert [segment["text"] for segment in segments] == [
        "kalimat pertama",
        "kalimat lain sama sekali",
        "kalimat pertama",
    ]
