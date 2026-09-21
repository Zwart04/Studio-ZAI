import pytest

from studiozai import config, projects, service


@pytest.fixture(autouse=True)
def isolate_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path / "StudioZAI")
    yield


def test_project_lifecycle():
    project = projects.Project.create("Test Klip", source="", language="id")
    assert project.project_file.exists()

    loaded = projects.load_project(project.id)
    assert loaded.title == "Test Klip"

    project.add_clip(projects.Clip(index=0, start=10.0, end=25.0, title="pertama"))
    project.add_clip(projects.Clip(index=1, start=30.0, end=50.0, title="kedua"))
    project.save()

    loaded = projects.load_project(project.id)
    assert [c.title for c in loaded.clips] == ["pertama", "kedua"]
    assert loaded.clips[0].duration == 15.0

    loaded.update_clip(0, {"title": "diubah", "crop": "blur"})
    assert loaded.clip(0).title == "diubah"
    assert loaded.clip(0).crop == "blur"

    loaded.move_clip(0, 1)
    assert [c.index for c in loaded.clips] == [0, 1]
    assert loaded.clips[0].title == "kedua"

    left, right = loaded.split_clip(0, 40.0)
    assert left.end == 40.0 and right.start == 40.0
    assert len(loaded.clips) == 3

    loaded.remove_clip(0)
    assert len(loaded.clips) == 2
    assert [c.index for c in loaded.clips] == [0, 1]


def test_undo_restores_previous_clips():
    project = projects.Project.create("Undo", language="id")
    project.add_clip(projects.Clip(index=0, start=0, end=10))
    project.remove_clip(0)
    assert project.clips == []
    assert project.undo() is True
    assert len(project.clips) == 1


def test_list_and_delete():
    first = projects.Project.create("A", language="id")
    projects.Project.create("B", language="id")
    assert {p.title for p in projects.list_projects()} == {"A", "B"}
    projects.delete_project(first.id)
    assert {p.title for p in projects.list_projects()} == {"B"}


def test_duplicate_project_copies_clips():
    project = projects.Project.create("Asli", language="id")
    project.add_clip(projects.Clip(index=0, start=1, end=5, title="x"))
    project.save()
    copy = projects.duplicate_project(project.id)
    assert copy.id != project.id
    assert copy.title.endswith("(salinan)")
    assert len(copy.clips) == 1


def test_captions_for_range_are_clip_relative():
    transcript = {
        "segments": [
            {
                "start": 100.0,
                "end": 104.0,
                "text": "halo dunia",
                "words": [
                    {"word": "halo", "start": 100.0, "end": 100.5},
                    {"word": "dunia", "start": 100.5, "end": 101.0},
                    {"word": "lain", "start": 110.0, "end": 110.5},
                ],
            }
        ]
    }
    captions = service.captions_for_range(transcript, 100.0, 105.0)
    assert captions
    assert captions[0]["start"] == 0.0
    assert "lain" not in captions[0]["text"]
    assert all(c["end"] <= 5.0 for c in captions)


def test_load_missing_project():
    with pytest.raises(KeyError):
        projects.load_project("tidakada")


def test_doctor_reports_problems_without_ffmpeg(monkeypatch):
    from studiozai.utils import ffmpeg

    monkeypatch.setattr(ffmpeg, "ffmpeg_available", lambda: False)
    report = service.doctor()
    assert any("FFmpeg" in p for p in report["problems"])
    assert "tier" in report and "hardware" in report
