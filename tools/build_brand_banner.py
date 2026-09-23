"""Rebuild the README banner from the unchanged Studio ZAI mark.

The white canvas keeps the original dark logo readable in either GitHub theme.
The banner is SVG so the typography stays sharp without another bitmap asset.
"""

from __future__ import annotations

import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
mark = base64.b64encode((ROOT / "assets" / "logo.png").read_bytes()).decode("ascii")
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="280" viewBox="0 0 1200 280" role="img" aria-label="Studio ZAI — Video, Suara, Gambar">
<rect width="1200" height="280" rx="28" fill="#f5f5f7"/>
<rect x="28" y="28" width="224" height="224" rx="24" fill="#ffffff"/>
<image x="56" y="77" width="168" height="126" href="data:image/png;base64,{mark}"/>
<text x="302" y="91" fill="#6e6e73" font-family="Arial,Helvetica,sans-serif" font-size="17" font-weight="700" letter-spacing="3">STUDIO KREATIF LOKAL</text>
<text x="299" y="171" fill="#1d1d1f" font-family="Arial,Helvetica,sans-serif" font-size="73" font-weight="700">Studio ZAI</text>
<text x="302" y="222" fill="#6e6e73" font-family="Arial,Helvetica,sans-serif" font-size="26">Video  ·  Suara  ·  Gambar</text>
</svg>
'''
(ROOT / "assets" / "brand-banner.svg").write_text(svg, encoding="utf-8")
