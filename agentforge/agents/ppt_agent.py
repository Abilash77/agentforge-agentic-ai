"""
AgentForge PPT Agent.

Generates professional presentation decks:
  - Startup pitch deck (10 slides)
  - Hackathon presentation (5 slides)
  - Investor presentation (15 slides)

Uses python-pptx for programmatic PowerPoint generation.
"""

from __future__ import annotations

import json
from typing import ClassVar, Optional

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class GeneratePitchDeckContent(Action):
    """Generate structured content for a startup pitch deck."""

    name: str = "GeneratePitchDeckContent"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a seasoned startup pitch coach and presentation expert who has helped companies raise millions.

## Project: {idea}
## Tech Stack: {tech_stack}
## Project Summary: {project_summary}

Generate a compelling 10-slide startup pitch deck content.

Return a JSON structure with this exact format:
```json
{{
  "title": "Company/Product Name",
  "tagline": "One compelling tagline",
  "deck_type": "startup_pitch",
  "slides": [
    {{
      "slide_number": 1,
      "title": "The Problem",
      "subtitle": "optional subtitle",
      "bullet_points": ["point 1", "point 2", "point 3"],
      "speaker_notes": "What to say during this slide...",
      "visual_suggestion": "Description of recommended visual/chart"
    }},
    ...
  ]
}}
```

Slides must cover:
1. **Title Slide** — Company name, tagline, presenter info
2. **The Problem** — Pain point with market validation data
3. **Our Solution** — Product/service with key differentiators
4. **Market Opportunity** — TAM/SAM/SOM with credible data
5. **Product Demo** — Key features and screenshots description
6. **Business Model** — Revenue streams, pricing strategy
7. **Traction** — Metrics, users, revenue (or projections)
8. **Competitive Analysis** — Competitive matrix
9. **Team** — Founders and key team with credentials
10. **The Ask** — Funding amount, use of funds, milestones

Make it compelling, data-driven, and investor-ready.
Return ONLY valid JSON.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            project_summary=kwargs.get("project_summary", "")[:2000],
        )
        content = await self._aask(prompt)
        # Clean JSON if wrapped in markdown code block
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content


class GenerateHackathonDeck(Action):
    """Generate content for a 5-slide hackathon presentation."""

    name: str = "GenerateHackathonDeck"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a hackathon presentation coach.

## Project: {idea}
## Tech Stack: {tech_stack}
## What was built: {project_summary}

Generate a compelling 5-slide hackathon presentation.

Return JSON with this structure:
```json
{{
  "title": "Project Name",
  "tagline": "Tagline",
  "deck_type": "hackathon",
  "team_name": "Team Name",
  "hackathon_theme": "Theme",
  "slides": [
    {{
      "slide_number": 1,
      "title": "Project Name",
      "subtitle": "Tagline",
      "bullet_points": [],
      "speaker_notes": "...",
      "visual_suggestion": "..."
    }}
  ]
}}
```

Slides:
1. **Project Title** — Name, tagline, team name, hackathon
2. **The Problem We Solved** — Problem statement with impact
3. **Our Solution** — What we built, key features, tech stack
4. **Live Demo** — Demo highlights and screenshots description
5. **Impact & Next Steps** — Impact metrics, future roadmap, team ask

Keep it punchy, visual, and demo-focused. Judges have 3 minutes.
Return ONLY valid JSON.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            project_summary=kwargs.get("project_summary", "")[:2000],
        )
        content = await self._aask(prompt)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content


class GenerateInvestorPresentation(Action):
    """Generate content for a 15-slide investor presentation."""

    name: str = "GenerateInvestorPresentation"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a seasoned investor presentation coach and former VC partner.

## Project: {idea}
## Tech Stack: {tech_stack}
## Project Details: {project_summary}

Generate a 15-slide Series A investor presentation.

Return JSON:
```json
{{
  "title": "Company Name",
  "tagline": "Tagline",
  "deck_type": "investor",
  "series": "Series A",
  "asking_amount": "$X million",
  "slides": [...]
}}
```

Slides:
1. Cover — Company, tagline, date
2. Executive Summary — The 30-second pitch
3. The Problem — Market pain with data
4. Solution — Product overview
5. Product Deep Dive — Features, UX, tech
6. Market Size — TAM/SAM/SOM analysis
7. Business Model — Revenue model, unit economics
8. Traction & Metrics — MoM growth, retention, NPS
9. Technology & IP — Technical moats, patents
10. Go-to-Market — Customer acquisition strategy
11. Competitive Landscape — Matrix comparison
12. Team — Founders, advisors, board
13. Financials — 3-year projections, key assumptions
14. The Ask — Amount, valuation, use of funds
15. Appendix — Supporting data

Return ONLY valid JSON.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            project_summary=kwargs.get("project_summary", "")[:2000],
        )
        content = await self._aask(prompt)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return content


def _generate_pptx_from_content(deck_content: dict) -> Optional[bytes]:
    """
    Generate a PowerPoint file from structured deck content.
    Returns bytes of the .pptx file or None if python-pptx not available.
    """
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.util import Inches, Pt

        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)

        # Color palette
        BG_COLOR = RGBColor(0x0D, 0x1B, 0x2A)   # Dark navy
        ACCENT_COLOR = RGBColor(0x00, 0xB4, 0xD8) # Cyan
        TEXT_COLOR = RGBColor(0xFF, 0xFF, 0xFF)    # White
        SUBTEXT_COLOR = RGBColor(0xAA, 0xC4, 0xE0) # Light blue-gray

        slides_data = deck_content.get("slides", [])

        for slide_data in slides_data:
            slide_layout = prs.slide_layouts[6]  # Blank layout
            slide = prs.slides.add_slide(slide_layout)

            # Background
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = BG_COLOR

            # Title
            title_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(0.4), Inches(12), Inches(1.2)
            )
            title_frame = title_box.text_frame
            title_frame.word_wrap = True
            title_para = title_frame.paragraphs[0]
            title_run = title_para.add_run()
            title_run.text = slide_data.get("title", "")
            title_run.font.size = Pt(36)
            title_run.font.bold = True
            title_run.font.color.rgb = ACCENT_COLOR

            # Subtitle (if any)
            if slide_data.get("subtitle"):
                sub_box = slide.shapes.add_textbox(
                    Inches(0.5), Inches(1.5), Inches(12), Inches(0.6)
                )
                sub_frame = sub_box.text_frame
                sub_para = sub_frame.paragraphs[0]
                sub_run = sub_para.add_run()
                sub_run.text = slide_data["subtitle"]
                sub_run.font.size = Pt(20)
                sub_run.font.color.rgb = SUBTEXT_COLOR

            # Bullet points
            bullets = slide_data.get("bullet_points", [])
            if bullets:
                content_box = slide.shapes.add_textbox(
                    Inches(0.5), Inches(2.2), Inches(9), Inches(4.5)
                )
                content_frame = content_box.text_frame
                content_frame.word_wrap = True
                for i, bullet in enumerate(bullets):
                    para = content_frame.add_paragraph() if i > 0 else content_frame.paragraphs[0]
                    para.space_before = Pt(6)
                    run = para.add_run()
                    run.text = f"• {bullet}"
                    run.font.size = Pt(18)
                    run.font.color.rgb = TEXT_COLOR

            # Visual suggestion in bottom right
            visual = slide_data.get("visual_suggestion", "")
            if visual:
                visual_box = slide.shapes.add_textbox(
                    Inches(9.5), Inches(2.2), Inches(3.3), Inches(4.5)
                )
                visual_frame = visual_box.text_frame
                visual_frame.word_wrap = True
                visual_para = visual_frame.paragraphs[0]
                visual_run = visual_para.add_run()
                visual_run.text = f"📊 {visual[:200]}"
                visual_run.font.size = Pt(11)
                visual_run.font.color.rgb = SUBTEXT_COLOR

            # Slide number
            num_box = slide.shapes.add_textbox(
                Inches(12), Inches(7.0), Inches(1), Inches(0.4)
            )
            num_frame = num_box.text_frame
            num_run = num_frame.paragraphs[0].add_run()
            num_run.text = str(slide_data.get("slide_number", ""))
            num_run.font.size = Pt(10)
            num_run.font.color.rgb = SUBTEXT_COLOR

        import io
        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()

    except ImportError:
        logger.warning("python-pptx not installed. PPTX generation skipped.")
        return None
    except Exception as e:
        logger.error(f"PPTX generation failed: {e}")
        return None


class PPTAgent(AgentForgeRole):
    """
    PPT Agent for AgentForge.

    Generates startup pitch decks, hackathon presentations,
    and investor presentations using python-pptx.
    """

    name: str = "Isabella"
    profile: str = "Presentation Designer"
    goal: str = (
        "Create compelling, professional presentation decks that effectively "
        "communicate the project's value proposition to different audiences."
    )
    constraints: str = (
        "Be persuasive and data-driven. "
        "Tailor content to the specific audience (investors, judges, etc.). "
        "Keep slides focused — one key message per slide."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([
            GeneratePitchDeckContent,
            GenerateHackathonDeck,
            GenerateInvestorPresentation,
        ])

    async def run_full_presentations(
        self,
        idea: str,
        tech_stack: str,
        pm_outputs: dict,
        arch_outputs: dict,
    ) -> dict[str, str]:
        """Execute the full PPT workflow."""
        project_summary = pm_outputs.get("brd", "")[:3000]

        await self.emit_progress("pitch_deck", 5, "Creating pitch deck...")
        await self._start_run_tracking("GeneratePitchDeckContent")
        pitch_action = GeneratePitchDeckContent(context=self.context)
        pitch_json = await pitch_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            project_summary=project_summary,
        )
        # Save JSON content
        await self.save_output(pitch_json, "pitch_deck_content.json", OutputType.PITCH_DECK)

        # Generate PPTX
        try:
            deck_data = json.loads(pitch_json)
            pptx_bytes = _generate_pptx_from_content(deck_data)
            if pptx_bytes:
                await self.save_output(
                    pptx_bytes.decode("latin-1"),
                    "startup_pitch_deck.pptx",
                    OutputType.PITCH_DECK,
                    index_in_rag=False,
                )
        except json.JSONDecodeError:
            logger.warning("Could not parse pitch deck JSON for PPTX generation")

        await self.emit_progress("pitch_complete", 33, "Pitch deck created ✓")

        await self._start_run_tracking("GenerateHackathonDeck")
        hackathon_action = GenerateHackathonDeck(context=self.context)
        hackathon_json = await hackathon_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            project_summary=project_summary,
        )
        await self.save_output(hackathon_json, "hackathon_deck_content.json", OutputType.HACKATHON_DECK)

        try:
            hackathon_data = json.loads(hackathon_json)
            pptx_bytes = _generate_pptx_from_content(hackathon_data)
            if pptx_bytes:
                await self.save_output(
                    pptx_bytes.decode("latin-1"),
                    "hackathon_presentation.pptx",
                    OutputType.HACKATHON_DECK,
                    index_in_rag=False,
                )
        except json.JSONDecodeError:
            pass

        await self.emit_progress("hackathon_complete", 66, "Hackathon deck created ✓")

        await self._start_run_tracking("GenerateInvestorPresentation")
        investor_action = GenerateInvestorPresentation(context=self.context)
        investor_json = await investor_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            project_summary=project_summary,
        )
        await self.save_output(investor_json, "investor_presentation_content.json", OutputType.INVESTOR_DECK)

        try:
            investor_data = json.loads(investor_json)
            pptx_bytes = _generate_pptx_from_content(investor_data)
            if pptx_bytes:
                await self.save_output(
                    pptx_bytes.decode("latin-1"),
                    "investor_presentation.pptx",
                    OutputType.INVESTOR_DECK,
                    index_in_rag=False,
                )
        except json.JSONDecodeError:
            pass

        await self.emit_progress("investor_complete", 100, "Investor presentation created ✓")

        return {
            "pitch_deck": pitch_json,
            "hackathon_deck": hackathon_json,
            "investor_deck": investor_json,
        }
