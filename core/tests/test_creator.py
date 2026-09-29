import copy

import pytest

from studiozai.pipeline import crop, highlight, podcast, subtitle, translation


def test_podcast_selects_complete_qa_over_advertisement():
    transcript = {"segments": [
        {"start": 0, "end": 15, "text": "Sponsor kami. Kode promo dan diskon di link di bio."},
        {"start": 15, "end": 45, "text": "Subscribe sekarang untuk promo code."},
        {"start": 50, "end": 60, "text": "Kenapa kamu akhirnya belajar dari kesalahan?"},
        {"start": 60, "end": 85, "text": "Dulu saya pernah gagal. Ternyata rahasia itu adalah pengalaman."},
        {"start": 85, "end": 100, "text": "Intinya, pelajaran ini memberi solusi."},
    ]}
    result = podcast.moments(transcript, 100, count=1)
    assert len(result) == 1
    assert result[0]["start"] == 50
    assert result[0]["end"] == 100
    assert "tanya-jawab" in result[0]["reason"]
    assert "Kenapa" in result[0]["title"]
    assert 0 <= result[0]["score"] <= 1


def test_word_style_roundtrip_and_safe_ass():
    row = subtitle.Caption(0, 2, "Halo dunia", [
        {"start": 0, "end": .7, "word": "Halo", "style": {"font": "Anton", "color": "#12ab34", "bold": True}},
        {"start": 1, "end": 2, "word": "dunia", "style": {"animation": "type"}},
    ], {"size": 72, "x": .5, "y": .7})
    assert subtitle.Caption(**row.as_dict()).as_dict() == row.as_dict()
    ass = subtitle.to_ass([row])
    assert r"\fnAnton" in ass and r"\c&H34ab12&" in ass and r"\b1" in ass
    assert r"\t(1000,1001,\alpha&H00&)" in ass
    assert r"\pos(540,1344)" in ass
    assert subtitle.to_srt([row]).endswith("Halo dunia\n")
    row.words[0]["style"]["font"] = r"Bad\fnInjected"
    assert "Injected" not in subtitle.to_ass([row])


def test_manual_crop_interpolates_clamped_keyframes():
    plan = crop.plan("manual", 1920, 1080, (1080, 1920), framing={
        "zoom": 1, "keyframes": [{"time": 0, "x": .2, "y": .5}, {"time": 2, "x": .8, "y": .5}]})
    assert "crop=606:1080" in plan.simple_chain
    assert "if(lt(t,2.000)" in plan.simple_chain
    assert "max(0,min(1314" in plan.simple_chain
    assert "scale=1080:1920" in plan.simple_chain


def test_split_shifts_words_languages_and_interpolated_crop():
    from studiozai import projects
    from studiozai.pipeline import timeline
    row = {"start": 1, "end": 3, "text": "Halo", "words": [{"word": "Halo", "start": 1, "end": 3}], "style": {"font": "Anton"}}
    clip = projects.Clip(0, 10, 14, captions=[row], caption_variants={"id": [row]})
    clip.timeline = timeline.default_timeline(10, 14, "video.mp4")
    timeline.track(clip.timeline, "video")[0]["framing"] = {"keyframes": [{"time": 0, "x": 0, "y": .5}, {"time": 4, "x": 1, "y": .5}]}
    project = projects.Project("test", "test", clips=[clip])
    _, right = project.split_clip(0, 12)
    assert right.captions[0]["words"][0]["start"] == 0
    assert right.caption_variants["id"][0]["end"] == 1
    assert timeline.track(right.timeline, "video")[0]["framing"]["keyframes"][0]["x"] == .5


def test_translation_preserves_cue_timing_and_style(monkeypatch):
    original = [{"start": 1., "end": 3., "text": "Halo", "words": [], "style": {"font": "Anton"}}]
    saved = copy.deepcopy(original)
    monkeypatch.setattr(translation, "translate_texts", lambda *args: ["Hello world"])
    result = translation.translate_captions(original, "id", "en")
    assert original == saved
    assert result[0]["start"] == 1 and result[0]["end"] == 3
    assert result[0]["style"] == original[0]["style"]
    assert [w["word"] for w in result[0]["words"]] == ["Hello", "world"]
    assert result[0]["words"][-1]["end"] == 3


def test_long_llm_input_is_bounded_and_overlaps_removed(monkeypatch):
    seen = []
    def rank(transcript, **kwargs):
        seen.append(transcript)
        return [{"start": 0, "end": 30, "score": .9, "title": "Hook", "reason": "QA"}]
    monkeypatch.setattr(highlight, "_rank_chunk", rank)
    rows = [{"start": i*10, "end": i*10+10, "text": "a "*250} for i in range(100)]
    result = highlight.rank_with_llm({"segments": rows}, count=0)
    assert len(seen) > 1 and len(result) == 1
    assert all(sum(len(r["text"])+40 for r in chunk["segments"]) <= 18000 for chunk in seen)


@pytest.mark.parametrize("mode", ["podcast", "auto"])
def test_review_first_does_not_render(monkeypatch, tmp_path, mode):
    from studiozai import config, projects, server, service
    monkeypatch.setattr(config, "_base_dir", lambda: tmp_path)
    project = projects.Project.create("Review")
    project.source = "source.mp4"
    project.save()
    def detect(p, **kwargs):
        assert kwargs["analysis_mode"] == mode
        p.clips = [projects.Clip(0, 0, 20)]
    monkeypatch.setattr(service, "generate_clips", detect)
    monkeypatch.setattr(service, "render_clip", lambda *a, **k: pytest.fail("Review must not render"))
    result = server._process_task(project.id, server.ProcessRequest(source="source.mp4", analysis_mode=mode))(None)
    assert result["clips"] == 1
