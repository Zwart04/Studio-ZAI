"""Uji penjagaan keamanan: id proyek dan ekstraksi arsip model."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from studiozai import projects
from studiozai.models import manager


@pytest.mark.parametrize("bad_id", ["..", ".", "../..", "a/b", "a\\b", "", "x" * 65, "C:"])
def test_project_id_traversal_ditolak(bad_id: str) -> None:
    with pytest.raises(KeyError):
        projects.load_project(bad_id)
    with pytest.raises(KeyError):
        projects.delete_project(bad_id)


def test_project_id_normal_diterima() -> None:
    # Id tidak ada -> KeyError "tidak ditemukan", bukan KeyError validasi.
    with pytest.raises(KeyError, match="tidak ditemukan"):
        projects.load_project("proyek_aman-123")


def test_delete_project_tidak_menghapus_folder_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "projects"
    base.mkdir()
    sentinel = base.parent / "penting.txt"
    sentinel.write_text("jangan dihapus", encoding="utf-8")
    monkeypatch.setattr(projects.config, "projects_dir", lambda: base)

    with pytest.raises(KeyError):
        projects.delete_project("..")
    assert sentinel.exists()


@pytest.mark.parametrize(
    "name",
    ["../evil.onnx", "/etc/passwd", "a/../../evil", "..\\evil", "C:/windows/x"],
)
def test_validate_members_menolak_path_berbahaya(tmp_path: Path, name: str) -> None:
    with pytest.raises(RuntimeError):
        manager._validate_members(tmp_path, [name])


def test_validate_members_menerima_nama_normal(tmp_path: Path) -> None:
    manager._validate_members(tmp_path, ["encoder.onnx", "sub/tokens.txt"])


def test_extract_zip_menolak_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "jahat.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../keluar.txt", "jahat")
    with pytest.raises(RuntimeError):
        manager._extract_archive(archive, tmp_path / "dest")
    assert not (tmp_path / "keluar.txt").exists()


def test_extract_tar_menolak_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "jahat.tar.gz"
    payload = b"jahat"
    info = tarfile.TarInfo("../keluar.txt")
    info.size = len(payload)
    with tarfile.open(archive, "w:gz") as handle:
        handle.addfile(info, io.BytesIO(payload))
    with pytest.raises(RuntimeError):
        manager._extract_archive(archive, tmp_path / "dest")
    assert not (tmp_path / "keluar.txt").exists()


def test_extract_tar_menolak_symlink(tmp_path: Path) -> None:
    archive = tmp_path / "link.tar.gz"
    info = tarfile.TarInfo("link")
    info.type = tarfile.SYMTYPE
    info.linkname = "/etc/passwd"
    with tarfile.open(archive, "w:gz") as handle:
        handle.addfile(info)
    with pytest.raises(RuntimeError):
        manager._extract_archive(archive, tmp_path / "dest")


def test_extract_zip_normal_berhasil(tmp_path: Path) -> None:
    archive = tmp_path / "baik.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("model.onnx", "bobot")
        handle.writestr("sub/tokens.txt", "token")
    dest = tmp_path / "dest"
    manager._extract_archive(archive, dest)
    assert (dest / "model.onnx").read_text(encoding="utf-8") == "bobot"
    assert (dest / "sub" / "tokens.txt").exists()
