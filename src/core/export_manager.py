import csv
import io
from datetime import date
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import ParagraphStyle
from src.core.detection_store import DetectionStore

class ExportManager:

    @staticmethod
    def export_csv(store: DetectionStore, output_path: str) -> None:
        records = store.get_all()
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "defect_id", "timestamp_sec", "timestamp_hms",
                "frame_number", "confidence", "x", "y", "width", "height"
            ])
            for r in records:
                x, y, w, h = r.bbox
                writer.writerow([
                    r.defect_id, f"{r.timestamp_sec:.2f}", r.timestamp_hms,
                    r.frame_number, f"{r.confidence:.2f}", x, y, w, h
                ])

    @staticmethod
    def export_pdf(
        store: DetectionStore,
        output_path: str,
        logo_path: str | None = None,
        video_filename: str = "",
    ) -> None:
        records = store.get_all()
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
        story = []

        title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold", spaceAfter=6)
        sub_style = ParagraphStyle("sub", fontSize=10, spaceAfter=20)

        if logo_path and Path(logo_path).exists():
            story.append(RLImage(logo_path, width=5*cm, height=1.5*cm))
            story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph("Pipe Defect Inspection Report", title_style))
        story.append(Paragraph(
            f"Video: {video_filename}  |  Date: {date.today()}  |  Total defects: {len(records)}",
            sub_style
        ))

        summary_data = [["#", "Timestamp", "Frame", "Confidence", "BBox (x,y,w,h)"]]
        for r in records:
            x, y, w, h = r.bbox
            summary_data.append([
                str(r.defect_id), r.timestamp_hms, str(r.frame_number),
                f"{r.confidence*100:.0f}%", f"({x},{y},{w},{h})"
            ])
        tbl = Table(summary_data, colWidths=[1.5*cm, 3*cm, 2.5*cm, 3*cm, 5*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 1*cm))

        for r in records:
            story.append(Paragraph(f"Defect #{r.defect_id}", ParagraphStyle(
                "defect_title", fontSize=13, fontName="Helvetica-Bold", spaceAfter=4
            )))
            if r.frame_image is not None:
                try:
                    import cv2
                    from PIL import Image as PILImage
                    frame = r.frame_image.copy()
                    x, y, w, h = r.bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    buf = io.BytesIO()
                    PILImage.fromarray(frame_rgb).save(buf, format="PNG")
                    buf.seek(0)
                    story.append(RLImage(buf, width=8*cm, height=5*cm))
                except Exception:
                    pass
            info_data = [
                ["Timestamp", r.timestamp_hms],
                ["Frame", str(r.frame_number)],
                ["Confidence", f"{r.confidence*100:.0f}%"],
                ["BBox (x,y,w,h)", str(r.bbox)],
            ]
            info_tbl = Table(info_data, colWidths=[4*cm, 10*cm])
            info_tbl.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(info_tbl)
            story.append(Spacer(1, 0.8*cm))

        doc.build(story)
