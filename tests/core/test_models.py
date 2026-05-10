from src.core.models import DefectRecord, VideoMetadata

def test_defect_record_creation():
    r = DefectRecord(
        track_id=1,
        timestamp_sec=83.4,
        frame_number=2502,
        confidence=0.87,
        bbox=(120, 340, 45, 38),
        frame_image=None,
    )
    assert r.timestamp_hms == "00:01:23"
    assert r.defect_id == 1

def test_video_metadata():
    m = VideoMetadata(fps=30.0, total_frames=9000, duration_sec=300.0, width=1920, height=1080)
    assert m.total_frames == 9000
