"""
Memora-Edge — PowerPoint Presentation Generator
Generates a premium hackathon pitch deck for Team Grey Coder.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# ── Colour palette ──────────────────────────────────────────────
BG_PRIMARY   = RGBColor(0x0B, 0x12, 0x20)
BG_CARD      = RGBColor(0x11, 0x18, 0x27)
ACCENT_BLUE  = RGBColor(0x25, 0x63, 0xEB)
ACCENT_TEAL  = RGBColor(0x14, 0xB8, 0xA6)
ACCENT_PURPLE= RGBColor(0x8B, 0x5C, 0xF6)
ACCENT_AMBER = RGBColor(0xF5, 0x9E, 0x0B)
ACCENT_RED   = RGBColor(0xEF, 0x44, 0x44)
TEXT_WHITE   = RGBColor(0xF1, 0xF5, 0xF9)
TEXT_LIGHT   = RGBColor(0x94, 0xA3, 0xB8)
TEXT_MUTED   = RGBColor(0x64, 0x74, 0x8B)
GREEN        = RGBColor(0x22, 0xC5, 0x5E)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

prs = Presentation()
prs.slide_width  = SLIDE_W
prs.slide_height = SLIDE_H

# ── Helpers ─────────────────────────────────────────────────────

def set_slide_bg(slide, color=BG_PRIMARY):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_shape(slide, left, top, width, height, fill_color, radius=Inches(0.15)):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape

def add_text_box(slide, left, top, width, height):
    return slide.shapes.add_textbox(left, top, width, height)

def set_text(tf, text, size=18, color=TEXT_WHITE, bold=False, align=PP_ALIGN.LEFT, font_name="Calibri"):
    tf.clear()
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font_name
    return p

def add_paragraph(tf, text, size=16, color=TEXT_WHITE, bold=False, space_before=Pt(6), space_after=Pt(2), font_name="Calibri"):
    p = tf.add_paragraph()
    p.space_before = space_before
    p.space_after  = space_after
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font_name
    return p

def add_bullet(tf, text, size=14, color=TEXT_LIGHT, level=0, font_name="Calibri"):
    p = tf.add_paragraph()
    p.level = level
    p.space_before = Pt(4)
    p.space_after  = Pt(2)
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = font_name
    return p

def accent_line(slide, left, top, width, color=ACCENT_BLUE):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Pt(4))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


# ════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
set_slide_bg(slide)

# Decorative gradient bar at top
accent_line(slide, Inches(0), Inches(0), SLIDE_W, ACCENT_BLUE)

# Logo circle
logo = add_shape(slide, Inches(5.9), Inches(1.8), Inches(1.5), Inches(1.5), ACCENT_BLUE)
tf = logo.text_frame
tf.word_wrap = True
tf.paragraphs[0].alignment = PP_ALIGN.CENTER
run = tf.paragraphs[0].add_run()
run.text = "M"
run.font.size = Pt(54)
run.font.color.rgb = TEXT_WHITE
run.font.bold = True
run.font.name = "Calibri"

# Title
tb = add_text_box(slide, Inches(2), Inches(3.6), Inches(9.3), Inches(1.2))
set_text(tb.text_frame, "Memora-Edge", size=52, bold=True, align=PP_ALIGN.CENTER)

# Tagline
tb = add_text_box(slide, Inches(2), Inches(4.7), Inches(9.3), Inches(0.7))
set_text(tb.text_frame, "Your AI Remembers. Even Offline.", size=24, color=ACCENT_TEAL, align=PP_ALIGN.CENTER)

# Team
tb = add_text_box(slide, Inches(2), Inches(5.7), Inches(9.3), Inches(0.5))
set_text(tb.text_frame, "Team Grey Coder  •  Paytm Hackathon", size=16, color=TEXT_MUTED, align=PP_ALIGN.CENTER)

# Bottom accent
accent_line(slide, Inches(0), Inches(7.45), SLIDE_W, ACCENT_TEAL)


# ════════════════════════════════════════════════════════════════
# SLIDE 2 — PROBLEM STATEMENT
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_RED)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "The Problem", size=36, bold=True)

tb = add_text_box(slide, Inches(0.8), Inches(2.0), Inches(11), Inches(5))
tf = tb.text_frame
tf.word_wrap = True

problems = [
    ("🌐  Cloud Dependency", "AI assistants fail when internet drops — unusable in remote sites, factories, field work."),
    ("🔒  Privacy Risks", "Sensitive data leaves the device and lives on third-party servers. No user control."),
    ("🧠  No Memory", "Conversations are forgotten between sessions. Users repeat themselves endlessly."),
    ("💸  Expensive APIs", "GPT-4 / Claude API costs scale fast — not viable for always-on edge deployments."),
]

for i, (title, desc) in enumerate(problems):
    add_paragraph(tf, title, size=20, bold=True, color=TEXT_WHITE, space_before=Pt(16 if i else 0))
    add_paragraph(tf, desc, size=15, color=TEXT_LIGHT, space_before=Pt(2))


# ════════════════════════════════════════════════════════════════
# SLIDE 3 — SOLUTION
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_TEAL)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Our Solution", size=36, bold=True)

tb = add_text_box(slide, Inches(0.8), Inches(2.0), Inches(11), Inches(1))
set_text(tb.text_frame, "An offline-first AI assistant with on-device semantic memory.", size=20, color=ACCENT_TEAL)

features = [
    ("🤖  AI Chat", "ChatGPT-like interface powered by local Ollama (Llama 3.2) — no internet needed"),
    ("🎙️  Voice Mode", "Push-to-talk via Faster Whisper + Piper TTS — real-time voice conversation"),
    ("🧠  Semantic Memory", "Every message stored as a vector embedding in Qdrant Edge — retrievable by meaning"),
    ("🔒  Privacy First", "Sensitive memories marked 'local_only' never leave the device"),
    ("📡  Smart Sync", "Only approved memories sync when connectivity returns"),
    ("📊  Dashboard", "Real-time analytics, memory stats, and sync activity at a glance"),
]

tb = add_text_box(slide, Inches(0.8), Inches(3.0), Inches(11.5), Inches(4.5))
tf = tb.text_frame
tf.word_wrap = True

for i, (title, desc) in enumerate(features):
    add_paragraph(tf, f"{title}  —  {desc}", size=15, color=TEXT_LIGHT, space_before=Pt(10 if i else 0))


# ════════════════════════════════════════════════════════════════
# SLIDE 4 — ARCHITECTURE
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_PURPLE)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "System Architecture", size=36, bold=True)

# Architecture boxes
boxes = [
    (Inches(1.0), Inches(2.2), Inches(3), Inches(1.5), ACCENT_BLUE,  "Frontend\nNext.js 15 • React • TS\nTailwind • Framer Motion"),
    (Inches(5.2), Inches(2.2), Inches(3), Inches(1.5), ACCENT_TEAL,  "Backend\nFastAPI • Python 3.11\n8 API Endpoints"),
    (Inches(9.4), Inches(2.2), Inches(3), Inches(1.5), ACCENT_PURPLE, "Storage\nQdrant Edge (vectors)\nSQLite (metadata)"),
]

for (l, t, w, h, clr, txt) in boxes:
    card = add_shape(slide, l, t, w, h, clr)
    card_tf = card.text_frame
    card_tf.word_wrap = True
    card_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    for j, line in enumerate(txt.split("\n")):
        if j == 0:
            run = card_tf.paragraphs[0].add_run()
            run.text = line
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = TEXT_WHITE
            run.font.name = "Calibri"
        else:
            p = card_tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            run = p.add_run()
            run.text = line
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(0xDE, 0xE8, 0xF0)
            run.font.name = "Calibri"

# Arrows between boxes
for x in [Inches(4.1), Inches(8.3)]:
    arrow = add_text_box(slide, x, Inches(2.7), Inches(1), Inches(0.5))
    set_text(arrow.text_frame, "→", size=28, color=TEXT_MUTED, align=PP_ALIGN.CENTER)

# Agents row
tb = add_text_box(slide, Inches(0.8), Inches(4.3), Inches(12), Inches(0.6))
set_text(tb.text_frame, "5 Modular AI Agents", size=22, bold=True, color=ACCENT_AMBER, align=PP_ALIGN.CENTER)

agent_data = [
    ("Memory", "Store +\nEmbed", ACCENT_BLUE),
    ("Retrieval", "Semantic\nSearch", ACCENT_TEAL),
    ("Classification", "Auto\nLabels", ACCENT_PURPLE),
    ("Sync", "Offline\nQueue", ACCENT_AMBER),
    ("Voice", "STT +\nTTS", ACCENT_RED),
]

for i, (name, desc, clr) in enumerate(agent_data):
    l = Inches(1.0 + i * 2.4)
    card = add_shape(slide, l, Inches(5.1), Inches(2.0), Inches(1.6), BG_CARD)
    # colored top bar
    accent_line(slide, l, Inches(5.1), Inches(2.0), clr)
    card_tf = card.text_frame
    card_tf.word_wrap = True
    card_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = card_tf.paragraphs[0].add_run()
    run.text = name
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = clr
    run.font.name = "Calibri"
    p = card_tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = desc
    run.font.size = Pt(11)
    run.font.color.rgb = TEXT_LIGHT
    run.font.name = "Calibri"


# ════════════════════════════════════════════════════════════════
# SLIDE 5 — MEMORY ARCHITECTURE
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_BLUE)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Memory Architecture", size=36, bold=True)

# Left side — Memory structure
tb = add_text_box(slide, Inches(0.8), Inches(2.0), Inches(5.5), Inches(5))
tf = tb.text_frame
tf.word_wrap = True
set_text(tf, "Each Memory Contains:", size=20, bold=True)

fields = [
    "UUID — unique identifier",
    "Original text — raw user input",
    "Embedding vector — 384-dim (bge-small-en-v1.5)",
    "Timestamp — creation time",
    "Source — chat / voice / manual",
    "Importance — critical / high / medium / low",
    "Privacy — local_only / sync_allowed",
    "Category — personal / work / maintenance / research / health",
    "Sync status — pending / synced",
]
for f in fields:
    add_bullet(tf, f"•  {f}", size=13, color=TEXT_LIGHT)

# Right side — Dual storage
card = add_shape(slide, Inches(7.0), Inches(2.0), Inches(5.5), Inches(2.0), BG_CARD)
card_tf = card.text_frame
card_tf.word_wrap = True
set_text(card_tf, "  🔷 Qdrant Edge", size=18, bold=True, color=ACCENT_BLUE)
add_paragraph(card_tf, "  Stores embedding vectors + metadata references", size=13, color=TEXT_LIGHT)
add_paragraph(card_tf, "  Enables semantic similarity search", size=13, color=TEXT_LIGHT)

card2 = add_shape(slide, Inches(7.0), Inches(4.4), Inches(5.5), Inches(2.0), BG_CARD)
card_tf2 = card2.text_frame
card_tf2.word_wrap = True
set_text(card_tf2, "  🟢 SQLite", size=18, bold=True, color=GREEN)
add_paragraph(card_tf2, "  Stores structured metadata for filtering", size=13, color=TEXT_LIGHT)
add_paragraph(card_tf2, "  Analytics, sync queue, conversation history", size=13, color=TEXT_LIGHT)


# ════════════════════════════════════════════════════════════════
# SLIDE 6 — SEMANTIC SEARCH DEMO
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_TEAL)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Semantic Memory in Action", size=36, bold=True)

# Store example
card = add_shape(slide, Inches(1.0), Inches(2.2), Inches(5.2), Inches(1.8), BG_CARD)
card_tf = card.text_frame
card_tf.word_wrap = True
set_text(card_tf, '  💬 User says:', size=14, color=TEXT_MUTED)
add_paragraph(card_tf, '  "Generator 5 has coolant leakage."', size=18, bold=True, color=TEXT_WHITE, space_before=Pt(10))
add_paragraph(card_tf, '  → Stored as 384-dim embedding in Qdrant Edge', size=12, color=ACCENT_BLUE, space_before=Pt(8))

# Arrow
tb = add_text_box(slide, Inches(5.5), Inches(2.8), Inches(2), Inches(0.8))
set_text(tb.text_frame, "  Later... →", size=16, color=ACCENT_AMBER, align=PP_ALIGN.CENTER)

# Search example
card2 = add_shape(slide, Inches(7.0), Inches(2.2), Inches(5.5), Inches(1.8), BG_CARD)
card_tf2 = card2.text_frame
card_tf2.word_wrap = True
set_text(card_tf2, '  🔍 User searches:', size=14, color=TEXT_MUTED)
add_paragraph(card_tf2, '  "Which machine has maintenance issues?"', size=18, bold=True, color=TEXT_WHITE, space_before=Pt(10))
add_paragraph(card_tf2, '  → Cosine similarity match: 94.2%', size=12, color=GREEN, space_before=Pt(8))

# Explanation
tb = add_text_box(slide, Inches(1.0), Inches(4.5), Inches(11.5), Inches(2.5))
tf = tb.text_frame
tf.word_wrap = True
set_text(tf, "How it works:", size=20, bold=True, color=ACCENT_TEAL)

steps = [
    "1.  Every message is converted to a 384-dimensional embedding using bge-small-en-v1.5",
    "2.  Embeddings are stored in Qdrant Edge (local vector database — no cloud needed)",
    "3.  Search queries are also embedded and compared using cosine similarity",
    "4.  Results are ranked by semantic relevance — not keyword matching",
    '5.  "coolant leakage" matches "maintenance issues" because they share meaning',
]
for s in steps:
    add_bullet(tf, s, size=14, color=TEXT_LIGHT)


# ════════════════════════════════════════════════════════════════
# SLIDE 7 — SMART SYNC ENGINE
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_AMBER)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Smart Sync Engine", size=36, bold=True)

# Three columns — LOCAL / PENDING / CLOUD
col_data = [
    ("🔒 LOCAL", "Never leaves device", ACCENT_PURPLE, ["Password: xyz123", "My salary is ...", "Private health note"]),
    ("⏳ PENDING", "Queued for sync", ACCENT_AMBER, ["Generator 5 needs...", "Project deadline...", "Meeting at 3 PM"]),
    ("☁️ CLOUD", "Synced to cloud", ACCENT_TEAL, ["Office hours update", "Team standup notes", "Research findings"]),
]

for i, (title, subtitle, clr, items) in enumerate(col_data):
    l = Inches(0.8 + i * 4.2)
    # Header card
    card = add_shape(slide, l, Inches(2.2), Inches(3.6), Inches(4.5), BG_CARD)
    accent_line(slide, l, Inches(2.2), Inches(3.6), clr)
    card_tf = card.text_frame
    card_tf.word_wrap = True
    card_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = card_tf.paragraphs[0].add_run()
    run.text = title
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = clr
    run.font.name = "Calibri"
    p = card_tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = subtitle
    run.font.size = Pt(11)
    run.font.color.rgb = TEXT_MUTED
    run.font.name = "Calibri"
    # Items
    for item in items:
        add_paragraph(card_tf, f"  •  {item}", size=13, color=TEXT_LIGHT, space_before=Pt(10))


# ════════════════════════════════════════════════════════════════
# SLIDE 8 — TECH STACK
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_BLUE)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Tech Stack", size=36, bold=True)

stack_data = [
    ("Frontend", "Next.js 15  •  React  •  TypeScript\nTailwind CSS  •  ShadCN UI  •  Framer Motion  •  Zustand", ACCENT_BLUE),
    ("Backend", "FastAPI  •  Python 3.11\nSQLAlchemy  •  async/await", ACCENT_TEAL),
    ("Vector DB", "Qdrant Edge — on-device\nSentence Transformers (bge-small-en-v1.5)", ACCENT_PURPLE),
    ("LLM", "Ollama — Llama 3.2\nFully local, no API costs", ACCENT_AMBER),
    ("Voice", "Faster Whisper (STT)\nPiper TTS (Speech Synthesis)", ACCENT_RED),
    ("Infra", "Docker Compose\nSQLite for metadata", TEXT_LIGHT),
]

for i, (label, desc, clr) in enumerate(stack_data):
    row = i // 3
    col = i % 3
    l = Inches(0.8 + col * 4.2)
    t = Inches(2.2 + row * 2.6)
    card = add_shape(slide, l, t, Inches(3.6), Inches(2.0), BG_CARD)
    accent_line(slide, l, t, Inches(3.6), clr)
    card_tf = card.text_frame
    card_tf.word_wrap = True
    set_text(card_tf, f"  {label}", size=18, bold=True, color=clr)
    for line in desc.split("\n"):
        add_paragraph(card_tf, f"  {line}", size=12, color=TEXT_LIGHT, space_before=Pt(4))


# ════════════════════════════════════════════════════════════════
# SLIDE 9 — LIVE DEMO FLOW
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), GREEN)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Live Demo Flow", size=36, bold=True)

demo_steps = [
    ("1", "Toggle OFF internet in Sync Center", "Simulate edge/offline environment", ACCENT_RED),
    ("2", 'Chat: "Remember that Generator 5\nneeds inspection tomorrow"', "AI responds + auto-classifies + stores locally", ACCENT_BLUE),
    ("3", 'Search: "Which generator needs\nmaintenance?"', "Semantic match found instantly — no keywords needed", ACCENT_TEAL),
    ("4", "Toggle ON internet", "Connection restored", GREEN),
    ("5", "Click Sync Now", "Pending memories animate → Cloud column", ACCENT_AMBER),
    ("6", "Check Dashboard", "Stats update in real time", ACCENT_PURPLE),
]

for i, (num, action, result, clr) in enumerate(demo_steps):
    row = i // 2
    col = i % 2
    l = Inches(0.8 + col * 6.3)
    t = Inches(2.0 + row * 1.75)
    
    # Number circle
    circle = add_shape(slide, l, t + Inches(0.15), Inches(0.55), Inches(0.55), clr)
    circle_tf = circle.text_frame
    circle_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = circle_tf.paragraphs[0].add_run()
    run.text = num
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = TEXT_WHITE
    run.font.name = "Calibri"
    
    # Text
    tb = add_text_box(slide, l + Inches(0.75), t, Inches(5.2), Inches(1.5))
    tf = tb.text_frame
    tf.word_wrap = True
    set_text(tf, action, size=14, bold=True, color=TEXT_WHITE)
    add_paragraph(tf, result, size=12, color=TEXT_LIGHT, space_before=Pt(4))


# ════════════════════════════════════════════════════════════════
# SLIDE 10 — PRIVACY & SECURITY
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(3), ACCENT_PURPLE)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(8), Inches(0.8))
set_text(tb.text_frame, "Privacy & Security", size=36, bold=True)

tb = add_text_box(slide, Inches(0.8), Inches(2.0), Inches(11.5), Inches(5))
tf = tb.text_frame
tf.word_wrap = True

privacy_items = [
    ("🔒  All data stays on-device by default", "No external API calls for core functionality"),
    ("🏷️  Privacy labels on every memory", "AI auto-classifies: local_only vs sync_allowed"),
    ("🚫  local_only memories NEVER leave the device", "Passwords, health data, financials are protected"),
    ("☁️  Only approved memories can sync", "User controls what goes to cloud"),
    ("💰  Zero API costs", "Ollama + Qdrant Edge + Sentence Transformers — all free, all local"),
    ("🐳  Docker isolation", "Each service runs in its own container"),
]

for i, (title, desc) in enumerate(privacy_items):
    add_paragraph(tf, title, size=18, bold=True, color=TEXT_WHITE, space_before=Pt(14 if i else 0))
    add_paragraph(tf, f"      {desc}", size=13, color=TEXT_LIGHT, space_before=Pt(2))


# ════════════════════════════════════════════════════════════════
# SLIDE 11 — QDRANT EDGE PRINCIPLES
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0.8), Inches(0.8), Inches(4), ACCENT_TEAL)

tb = add_text_box(slide, Inches(0.8), Inches(0.95), Inches(10), Inches(0.8))
set_text(tb.text_frame, "Qdrant Edge Principles Applied", size=36, bold=True)

tb = add_text_box(slide, Inches(0.8), Inches(1.8), Inches(11.5), Inches(0.6))
set_text(tb.text_frame, "Inspired by DeepLearning.AI × Qdrant: Building AI Assistants with On-Device Memory", size=14, color=ACCENT_TEAL)

principles = [
    ("On-Device Semantic Memory", "All embeddings stored locally in Qdrant Edge — no cloud vector DB needed"),
    ("Local Vector Collections", "Separate local_memory and cloud_memory collections for privacy isolation"),
    ("Memory Lifecycle Management", "Create → Classify → Store → Search → Sync → Archive"),
    ("Semantic Retrieval", "Cosine similarity search over 384-dim embeddings, not keyword matching"),
    ("Hybrid Search", "Vector similarity + metadata filters (category, importance, privacy)"),
    ("Memory Importance", "AI-classified importance scores drive prioritization and visibility"),
    ("Offline-First Architecture", "Everything works without internet — sync is optional, not required"),
    ("Intelligent Synchronization", "Privacy-aware sync: only approved memories, with conflict tracking"),
]

tb = add_text_box(slide, Inches(0.8), Inches(2.5), Inches(11.5), Inches(4.5))
tf = tb.text_frame
tf.word_wrap = True

for i, (title, desc) in enumerate(principles):
    add_paragraph(tf, f"✦  {title}", size=15, bold=True, color=TEXT_WHITE, space_before=Pt(8 if i else 0))
    add_paragraph(tf, f"     {desc}", size=12, color=TEXT_LIGHT, space_before=Pt(1))


# ════════════════════════════════════════════════════════════════
# SLIDE 12 — THANK YOU
# ════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(slide)
accent_line(slide, Inches(0), Inches(0), SLIDE_W, ACCENT_BLUE)

tb = add_text_box(slide, Inches(2), Inches(2.0), Inches(9.3), Inches(1.2))
set_text(tb.text_frame, "Thank You!", size=52, bold=True, align=PP_ALIGN.CENTER)

tb = add_text_box(slide, Inches(2), Inches(3.3), Inches(9.3), Inches(0.7))
set_text(tb.text_frame, "Your AI Remembers. Even Offline.", size=24, color=ACCENT_TEAL, align=PP_ALIGN.CENTER)

tb = add_text_box(slide, Inches(2), Inches(4.5), Inches(9.3), Inches(2.5))
tf = tb.text_frame
tf.word_wrap = True
set_text(tf, "Team Grey Coder", size=22, bold=True, align=PP_ALIGN.CENTER)
add_paragraph(tf, "", size=8)
add_paragraph(tf, "Memora-Edge v1.0", size=16, color=ACCENT_BLUE, space_before=Pt(12))
tf.paragraphs[-1].alignment = PP_ALIGN.CENTER
add_paragraph(tf, "Paytm Hackathon", size=16, color=TEXT_MUTED, space_before=Pt(6))
tf.paragraphs[-1].alignment = PP_ALIGN.CENTER
add_paragraph(tf, "", size=8)
add_paragraph(tf, "Next.js  •  FastAPI  •  Qdrant Edge  •  Ollama  •  Sentence Transformers", size=12, color=TEXT_MUTED, space_before=Pt(16))
tf.paragraphs[-1].alignment = PP_ALIGN.CENTER

accent_line(slide, Inches(0), Inches(7.45), SLIDE_W, ACCENT_TEAL)


# ════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════
out_dir = os.path.join(os.path.dirname(__file__))
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "Memora-Edge-Pitch-Deck.pptx")
prs.save(out_path)
print(f"✅ Presentation saved to: {out_path}")
print(f"   Slides: {len(prs.slides)}")
