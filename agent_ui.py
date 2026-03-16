"""
PLUTO — AI System Agent UI
Communicates with main.py via subprocess stdin/stdout.
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import sys
import os
import queue
import re

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON  = os.path.join(BASE_DIR, "ai_agent", "Scripts", "python.exe")
PYTHON       = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable
AGENT_SCRIPT = os.path.join(BASE_DIR, "main.py")
USER_NAME    = "Natansh"

# ── Palette ────────────────────────────────────────────────────────────────
BG          = "#111118"
CARD        = "#1C1C28"
CARD2       = "#21212F"
CARD3       = "#18181F"          # log drawer background
BORDER      = "#2A2A3A"
BORDER_LT   = "#333348"
ACCENT      = "#7C6AF7"
ACCENT2     = "#A78BFA"
ACCENT_GLOW = "#4C3DBF"
TEXT_HI     = "#F0EFFF"
TEXT        = "#C8C8E0"
TEXT_DIM    = "#55556A"
TEXT_TINY   = "#3D3D55"
GREEN       = "#34D399"
AMBER       = "#FBBF24"
RED         = "#F87171"
CODE_BG     = "#1A1A2E"
CODE_FG     = "#A8D8A8"

# ── Fonts ──────────────────────────────────────────────────────────────────
F_HEADER    = ("Georgia", 16, "bold")
F_SUB       = ("Calibri", 12)
F_BODY      = ("Calibri", 15)
F_BODY_SM   = ("Calibri", 13)
F_MONO      = ("Consolas", 10)
F_MONO_SM   = ("Consolas", 9)
F_INPUT     = ("Calibri", 15)
F_BTN       = ("Calibri", 11, "bold")
F_LOG_HDR   = ("Calibri", 9)
F_H1        = ("Georgia", 18, "bold")
F_H2        = ("Georgia", 15, "bold")
F_H3        = ("Calibri", 13, "bold")
F_CODE      = ("Consolas", 11)
F_BOLD      = ("Calibri", 12, "bold")
F_ITALIC    = ("Calibri", 12, "italic")


# ── Markdown renderer ──────────────────────────────────────────────────────

def render_markdown(widget: tk.Text, text: str, lmargin: int = 20, rmargin: int = 160):
    """
    Parse and insert markdown-formatted text into a tk.Text widget.
    Handles: # headings, **bold**, *italic*, `inline code`, ```blocks```, - lists, > blockquotes.
    Falls back to plain text insertion if parsing fails.
    """
    try:
        _render_markdown_inner(widget, text, lmargin, rmargin)
    except Exception:
        # Nuclear fallback — always show something
        widget.insert("end", text + "\n", "md_body")


def _render_markdown_inner(widget: tk.Text, text: str, lmargin: int, rmargin: int):
    lines = text.split("\n")
    in_code_block = False
    code_lines = []
    code_lang = ""

    for line in lines:
        # ── Code block open/close ──────────────────────────────────────
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                code_lines = []
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                # Insert code block with background-like indentation
                widget.insert("end", "\n", "md_pad")
                widget.insert("end", code_text + "\n", "md_code")
                widget.insert("end", "\n", "md_pad")
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # ── Headings ──────────────────────────────────────────────────
        h3 = re.match(r"^### (.+)", line)
        h2 = re.match(r"^## (.+)", line)
        h1 = re.match(r"^# (.+)", line)
        if h1:
            widget.insert("end", h1.group(1) + "\n", "md_h1")
            continue
        if h2:
            widget.insert("end", h2.group(1) + "\n", "md_h2")
            continue
        if h3:
            widget.insert("end", h3.group(1) + "\n", "md_h3")
            continue

        # ── Blockquote ────────────────────────────────────────────────
        bq = re.match(r"^> (.+)", line)
        if bq:
            widget.insert("end", "  " + bq.group(1) + "\n", "md_bq")
            continue

        # ── List item ─────────────────────────────────────────────────
        li = re.match(r"^[-*+] (.+)", line)
        if li:
            _insert_inline(widget, "  • " + li.group(1) + "\n", lmargin, rmargin)
            continue

        # ── Numbered list ─────────────────────────────────────────────
        nl = re.match(r"^(\d+)\. (.+)", line)
        if nl:
            _insert_inline(widget, f"  {nl.group(1)}. {nl.group(2)}\n", lmargin, rmargin)
            continue

        # ── Horizontal rule ───────────────────────────────────────────
        if re.match(r"^[-*_]{3,}$", line.strip()):
            widget.insert("end", "\n", "md_pad")
            continue

        # ── Empty line ────────────────────────────────────────────────
        if not line.strip():
            widget.insert("end", "\n", "md_pad")
            continue

        # ── Normal paragraph with inline markup ───────────────────────
        _insert_inline(widget, line + "\n", lmargin, rmargin)

    # Flush any unclosed code block
    if in_code_block and code_lines:
        widget.insert("end", "\n", "md_pad")
        widget.insert("end", "\n".join(code_lines) + "\n", "md_code")
        widget.insert("end", "\n", "md_pad")


def _insert_inline(widget: tk.Text, text: str, lmargin: int, rmargin: int):
    """Insert a line with inline **bold**, *italic*, `code` handled."""
    # Use word-boundary aware patterns to avoid matching * inside words/strings
    pattern = re.compile(r"(\*\*(.+?)\*\*|(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)|`(.+?)`)")
    pos = 0
    try:
        for m in pattern.finditer(text):
            before = text[pos:m.start()]
            if before:
                widget.insert("end", before, ("md_body",))
            full = m.group(0)
            if full.startswith("**"):
                widget.insert("end", m.group(2), "md_bold")
            elif full.startswith("`"):
                widget.insert("end", m.group(4), "md_inline_code")
            elif full.startswith("*"):
                widget.insert("end", m.group(3), "md_italic")
            pos = m.end()
        remainder = text[pos:]
        if remainder:
            widget.insert("end", remainder, "md_body")
    except Exception:
        # Fallback: insert entire line as plain body text
        widget.insert("end", text, "md_body")


def _configure_md_tags(widget: tk.Text, lmargin: int = 20, rmargin: int = 160):
    """Register all markdown tags on a Text widget."""
    widget.tag_config("md_h1",
        foreground=TEXT_HI, font=F_H1,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin,
        spacing1=10, spacing3=6)
    widget.tag_config("md_h2",
        foreground=ACCENT2, font=F_H2,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin,
        spacing1=8, spacing3=4)
    widget.tag_config("md_h3",
        foreground=TEXT_HI, font=F_H3,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin,
        spacing1=6, spacing3=2)
    widget.tag_config("md_body",
        foreground=TEXT, font=F_BODY,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin)
    widget.tag_config("md_bold",
        foreground=TEXT_HI, font=F_BOLD,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin)
    widget.tag_config("md_italic",
        foreground=TEXT, font=F_ITALIC,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin)
    widget.tag_config("md_inline_code",
        foreground=CODE_FG, font=F_CODE,
        lmargin1=lmargin, lmargin2=lmargin, rmargin=rmargin)
    widget.tag_config("md_code",
        foreground=CODE_FG, font=F_CODE,
        lmargin1=lmargin + 10, lmargin2=lmargin + 10,
        rmargin=rmargin, spacing1=2, spacing3=2,
        background=CODE_BG)
    widget.tag_config("md_bq",
        foreground=TEXT_DIM, font=("Calibri", 12, "italic"),
        lmargin1=lmargin + 16, lmargin2=lmargin + 16, rmargin=rmargin)
    widget.tag_config("md_pad", font=("Calibri", 4))


class AgentUI:
    def __init__(self, root: tk.Tk):
        self.root         = root
        self.proc         = None
        self.q            = queue.Queue()
        self.working      = False
        self._restarting  = False
        self._confirming  = False

        # Log drawer state
        self._log_buffer: list[str] = []
        self._log_group_count = 0  # for unique tag names

        self._build_window()
        self._build_ui()
        self._start_agent()
        self._poll_queue()

    # ── Window ────────────────────────────────────────────────────────────

    def _build_window(self):
        self.root.title("Pluto")
        self.root.configure(bg=BG)
        self.root.geometry("880x680")
        self.root.minsize(640, 460)
        self.root.resizable(True, True)
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=CARD)
        hdr.pack(fill="x")

        left = tk.Frame(hdr, bg=CARD)
        left.pack(side="left", padx=20, pady=12)

        avatar = tk.Canvas(left, width=36, height=36, bg=CARD,
                           highlightthickness=0)
        avatar.pack(side="left", anchor="center")
        avatar.create_oval(1, 1, 35, 35, fill=ACCENT_GLOW, outline="")
        avatar.create_oval(5, 5, 31, 31, fill=ACCENT, outline="")
        avatar.create_text(18, 18, text="P", fill=TEXT_HI,
                           font=("Georgia", 13, "bold"))

        name_col = tk.Frame(left, bg=CARD)
        name_col.pack(side="left", padx=(12, 0), anchor="center")
        tk.Label(name_col, text="Pluto", fg=TEXT_HI, bg=CARD,
                 font=F_HEADER).pack(anchor="w")
        # self.subtitle = tk.Label(name_col, text="",
        #                          fg=TEXT_DIM, bg=CARD, font=F_SUB)
        # self.subtitle.pack(anchor="w")

        # ── Gradient rule ──────────────────────────────────────────────────
        self._rule_canvas = tk.Canvas(self.root, height=2, bg=BG,
                                      highlightthickness=0)
        self._rule_canvas.pack(fill="x")
        self.root.after(120, self._draw_rule)
        self.root.bind("<Configure>", lambda e: self.root.after(50, self._draw_rule))

        # ── Confirm buttons (bottom, hidden) ──────────────────────────────
        self.confirm_frame = tk.Frame(self.root, bg=CARD2)
        cf = tk.Frame(self.confirm_frame, bg=CARD2)
        cf.pack(expand=True, fill="both", padx=20, pady=10)
        tk.Label(cf, text="⚠  Allow this action?", fg=AMBER, bg=CARD2,
                 font=("Calibri", 11, "bold")).pack(side="left", padx=(0, 18))
        tk.Button(cf, text="Allow", fg=BG, bg=GREEN, font=F_BTN,
                  bd=0, relief="flat", padx=18, cursor="hand2",
                  activebackground="#22C55E",
                  command=lambda: self._send_confirm("yes")).pack(
                      side="left", padx=(0, 8), ipady=5)
        tk.Button(cf, text="Deny", fg=RED, bg=CARD, font=F_BTN,
                  bd=0, relief="flat", padx=18, cursor="hand2",
                  activebackground=CARD2,
                  command=lambda: self._send_confirm("no")).pack(
                      side="left", ipady=5)

        # Bottom border + input — packed BEFORE chat so they're always visible
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", side="bottom")

        input_row = tk.Frame(self.root, bg=CARD)
        input_row.pack(fill="x", side="bottom")

        self._input_box = tk.Frame(input_row, bg=CARD2,
                                   highlightbackground=BORDER_LT,
                                   highlightthickness=1)
        self._input_box.pack(fill="x", padx=18, pady=14, ipady=2)

        self.input_var = tk.StringVar()
        self.entry = tk.Entry(self._input_box, textvariable=self.input_var,
                              bg=CARD2, fg=TEXT_HI, font=F_INPUT,
                              bd=0, relief="flat", insertbackground=ACCENT2,
                              disabledbackground=CARD2, disabledforeground=TEXT_DIM)
        self.entry.pack(side="left", fill="both", expand=True,
                        padx=(14, 0), pady=9)
        self.entry.bind("<Return>",   self._on_send)
        self.entry.bind("<Up>",       self._history_up)
        self.entry.bind("<Down>",     self._history_down)
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.focus_set()

        self.send_btn = tk.Button(self._input_box, text="↑",
                                  fg=TEXT_HI, bg=ACCENT, font=("Georgia", 14),
                                  bd=0, relief="flat", width=3,
                                  activebackground=ACCENT2, activeforeground=TEXT_HI,
                                  cursor="hand2", command=self._on_send)
        self.send_btn.pack(side="right", padx=6, pady=5, ipady=2)

        self._hint_active = True
        self.entry.insert(0, "Message Pluto…")
        self.entry.config(fg=TEXT_DIM)
        self._history     = []
        self._history_pos = -1

        # ── Thinking bar (hidden, shown above input) ───────────────────────
        self.thinking_bar = tk.Frame(self.root, bg=CARD2)
        think_inner = tk.Frame(self.thinking_bar, bg=CARD2)
        think_inner.pack(side="left", padx=20, pady=8)

        # Rotating cog canvas
        self._cog_canvas = tk.Canvas(think_inner, width=18, height=18,
                                     bg=CARD2, highlightthickness=0)
        self._cog_canvas.pack(side="left", padx=(0, 8))
        self._cog_angle = 0

        tk.Label(think_inner, text="Pluto is working",
                 fg=TEXT_DIM, bg=CARD2, font=F_BODY_SM).pack(side="left")

        # ── Chat area — packed LAST ────────────────────────────────────────
        chat_outer = tk.Frame(self.root, bg=BG)
        chat_outer.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(chat_outer, orient="vertical",
                                 bg=CARD2, troughcolor=BG,
                                 activebackground=BORDER,
                                 highlightthickness=0, bd=0, width=5)
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=6)

        self.chat = tk.Text(
            chat_outer, bg=BG, fg=TEXT, font=F_BODY,
            wrap=tk.WORD, bd=0, relief="flat", padx=0, pady=12,
            insertbackground=ACCENT, selectbackground=ACCENT_GLOW,
            state="disabled", cursor="arrow", spacing1=2, spacing3=4,
            yscrollcommand=scrollbar.set,
        )
        self.chat.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.chat.yview)

        # ── Static tags ───────────────────────────────────────────────────
        self.chat.tag_config("user_lbl",
            foreground=ACCENT2, font=("Calibri", 9, "bold"),
            justify="right", rmargin=20)
        self.chat.tag_config("user_msg",
            foreground=TEXT_HI, font=F_BODY,
            justify="right", lmargin1=160, lmargin2=160, rmargin=20,
            spacing1=2, spacing3=6)
        self.chat.tag_config("agent_lbl",
            foreground=GREEN, font=("Calibri", 9, "bold"), lmargin1=20)
        self.chat.tag_config("sys_msg",
            foreground=TEXT_DIM, font=F_MONO_SM, lmargin1=20, lmargin2=20)
        self.chat.tag_config("err_msg",
            foreground=RED, font=F_MONO_SM, lmargin1=20, lmargin2=20)
        self.chat.tag_config("warn_msg",
            foreground=AMBER, font=F_MONO_SM, lmargin1=20, lmargin2=20)
        self.chat.tag_config("out_msg",
            foreground=TEXT_HI, font=("Consolas", 11, "bold"),
            lmargin1=20, lmargin2=20)
        self.chat.tag_config("confirm",
            foreground=AMBER, font=("Calibri", 11, "bold"), lmargin1=20)
        self.chat.tag_config("center",
            justify="center", foreground=TEXT_DIM, font=("Georgia", 18),
            spacing1=4, spacing3=4)
        self.chat.tag_config("greeting",
            foreground=ACCENT2, font=("Georgia", 32, "bold"),
            justify="center", spacing1=18, spacing3=8)
        self.chat.tag_config("pad", font=("Calibri", 3))

        # Register markdown tags
        _configure_md_tags(self.chat, lmargin=20, rmargin=160)

    # ── Gradient rule ─────────────────────────────────────────────────────

    def _draw_rule(self):
        c = self._rule_canvas
        w = self.root.winfo_width()
        c.config(width=w)
        c.delete("all")
        steps = 30
        for i in range(steps):
            t  = i / steps
            r  = int(0x7C + (0x11 - 0x7C) * t)
            g  = int(0x6A + (0x11 - 0x6A) * t)
            b  = int(0xF7 + (0x18 - 0xF7) * t)
            x0 = int(w * i / steps)
            x1 = int(w * (i + 1) / steps)
            c.create_rectangle(x0, 0, x1, 2,
                               fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

    # ── Collapsible log drawer ─────────────────────────────────────────────

    def _flush_log_buffer(self, label: str = "Activity log"):
        """Take whatever is in _log_buffer and create a collapsible drawer."""
        if not self._log_buffer:
            return
        lines = list(self._log_buffer)
        self._log_buffer.clear()
        self._insert_log_drawer(label, lines)

    def _insert_log_drawer(self, label: str, lines: list[str]):
        """
        Insert a collapsible log section using pure text tags — no embedded
        frames, so it's fast regardless of log volume.
        Click the header line to expand/collapse.
        """
        self.chat.configure(state="normal")

        # Unique tag names for this drawer instance
        idx   = self._log_group_count
        self._log_group_count += 1
        h_tag = f"log_hdr_{idx}"
        b_tag = f"log_body_{idx}"

        state = {"expanded": False}

        # Header line
        header_text = f"  ▶  {label}  ({len(lines)} lines)\n"
        self.chat.insert("end", "\n", "pad")
        self.chat.insert("end", header_text, (h_tag,))

        # Body lines (inserted but elided/hidden by default)
        body_start = self.chat.index("end")
        for ln in lines:
            self.chat.insert("end", f"    {ln}\n", (b_tag,))
        body_end = self.chat.index("end")

        # Style tags
        self.chat.tag_config(h_tag,
            foreground=TEXT_DIM, font=("Calibri", 9, "italic"),
            lmargin1=20, spacing1=2, spacing3=2)
        self.chat.tag_config(b_tag,
            foreground=TEXT_TINY, font=F_MONO_SM,
            lmargin1=36, lmargin2=36, elide=True)

        self.chat.tag_bind(h_tag, "<Button-1>",
            lambda e, bt=b_tag, ht=h_tag, lbl=label, n=len(lines), s=state:
                self._toggle_log(bt, ht, lbl, n, s))
        self.chat.tag_bind(h_tag, "<Enter>",
            lambda e: self.chat.config(cursor="hand2"))
        self.chat.tag_bind(h_tag, "<Leave>",
            lambda e: self.chat.config(cursor="arrow"))

        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _toggle_log(self, body_tag, hdr_tag, label, count, state):
        state["expanded"] = not state["expanded"]
        arrow = "▼" if state["expanded"] else "▶"
        self.chat.configure(state="normal")
        self.chat.tag_config(body_tag, elide=not state["expanded"])
        ranges = self.chat.tag_ranges(hdr_tag)
        if ranges:
            self.chat.delete(ranges[0], ranges[1])
            new_hdr = f"  {arrow}  {label}  ({count} lines)\n"
            self.chat.insert(ranges[0], new_hdr, (hdr_tag,))
        self.chat.configure(state="disabled")

    # ── Agent process ─────────────────────────────────────────────────────

    def _start_agent(self):
        try:
            self.proc = subprocess.Popen(
                [PYTHON, "-u", AGENT_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1, cwd=BASE_DIR,
                creationflags=(subprocess.CREATE_NO_WINDOW
                               if sys.platform == "win32" else 0),
            )
            threading.Thread(target=self._read_output, daemon=True).start()
            if not self._restarting:
                self._insert_greeting()
            else:
                self._system_msg("Reconnected")
                self._restarting = False
        except Exception as e:
            self._append_raw("err_msg", f"Failed to start agent: {e}\n")

    def _insert_greeting(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\nHello, {USER_NAME}! \n", "greeting")
        self.chat.insert("end",
            "I'm Pluto, your personal AI agent. What can I do for you today?\n",
            "center")
        self.chat.insert("end", "\n", "pad")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _read_output(self):
        for line in self.proc.stdout:
            self.q.put(("line", line))
        self.q.put(("eof", None))

    # ── Queue polling ─────────────────────────────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == "line":
                    self._handle_line(data)
                elif kind == "eof":
                    self._flush_log_buffer("Session logs")
                    self._set_working(False)
                    self._enable_input()
                    self._system_msg("Agent stopped — restarting…")
                    self._restarting = True
                    self.root.after(1500, self._start_agent)
        except queue.Empty:
            pass
        self.root.after(40, self._poll_queue)

    def _handle_line(self, line: str):
        s = line.rstrip("\n")

        # ── Confirmation prompt ────────────────────────────────────────────
        if "Proceed?" in s:
            self._flush_log_buffer("Action details")
            self._show_confirm_buttons()
            return

        if s.startswith("Action:") or s.startswith("Risk Level:") or s.startswith("Description:"):
            self._log_buffer.append(s)
            return

        if "Script Preview" in s or s.startswith("--- Script") or s.startswith("--------"):
            self._log_buffer.append(s)
            return

        # ── Ready for input ────────────────────────────────────────────────
        if "What would you like to do?" in s:
            self._enable_input()
            return

        # ── Agent response ─────────────────────────────────────────────────
        if s.startswith("Agent Response:"):
            self._flush_log_buffer("Agent thoughts")
            self._set_working(False)

            msg = s.replace("Agent Response:", "").strip()

            # Collect following lines that belong to the response
            extra_lines = []
            while True:
                try:
                    nxt = self.q.get_nowait()[1].rstrip("\n")
                    if nxt.strip() == "":
                        break
                    extra_lines.append(nxt)
                except queue.Empty:
                    break

            if extra_lines:
                msg += "\n" + "\n".join(extra_lines)

            self._agent_bubble(msg)
            return

        # ── Script output ──────────────────────────────────────────────────
        if s.startswith("Script Output:"):
            self._flush_log_buffer("Run logs")
            out = s.replace("Script Output:", "").strip()
            self.chat.configure(state="normal")
            self.chat.insert("end", "\n", "pad")
            self.chat.insert("end", "  ✓  Output\n", "warn_msg")
            render_markdown(self.chat, out, lmargin=20, rmargin=160)
            self.chat.configure(state="disabled")
            self.chat.see("end")
            return

        if s.startswith("Script error:"):
            self._flush_log_buffer("Run logs")
            self._append_raw("err_msg", f"  ✕  {s}\n")
            return

        # ── Internal lines → log buffer ───────────────────────────────────
        noisy = ("[LLM", "[Tool Result]", "[Directive", "[Rephrased",
                 "[Updated State]", "[Extracted", "Goodbye!")
        if any(s.startswith(p) for p in noisy):
            self._log_buffer.append(s)
            return

        if s.startswith("[Loop Guard]") or s.startswith("[Arg Injection]"):
            self._log_buffer.append(s)
            return

        # ── Errors — always show immediately ──────────────────────────────
        if "Traceback" in s or s.startswith("  File "):
            self._flush_log_buffer()
            self._append_raw("err_msg", s + "\n")
            return

        if "error" in s.lower() and s.strip():
            self._append_raw("err_msg", s + "\n")
            return

        # ── Everything else → log buffer ──────────────────────────────────
        if s.strip():
            self._log_buffer.append(s)

    # ── Bubble rendering ──────────────────────────────────────────────────

    def _user_bubble(self, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", "\n", "pad")
        self.chat.insert("end", "You\n", "user_lbl")
        self.chat.insert("end", text + "\n", "user_msg")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _agent_bubble(self, text: str):
        """Render agent response with markdown support."""
        self.chat.configure(state="normal")
        self.chat.insert("end", "\n", "pad")
        self.chat.insert("end", "  Pluto\n", "agent_lbl")
        render_markdown(self.chat, text, lmargin=20, rmargin=160)
        self.chat.insert("end", "\n", "pad")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _system_msg(self, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"  —  {text}  —\n", "center")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _append_raw(self, tag: str, text: str):
        self.chat.configure(state="normal")
        self.chat.insert("end", text, tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    # ── Input hint ────────────────────────────────────────────────────────

    def _on_focus_in(self, event=None):
        self._input_box.config(highlightbackground=ACCENT)
        if self._hint_active:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT_HI)
            self._hint_active = False

    def _on_focus_out(self, event=None):
        self._input_box.config(highlightbackground=BORDER_LT)
        if not self.input_var.get():
            self.entry.insert(0, "Message Pluto…")
            self.entry.config(fg=TEXT_DIM)
            self._hint_active = True

    # ── Send ──────────────────────────────────────────────────────────────

    def _on_send(self, event=None):
        if self._hint_active:
            return
        text = self.input_var.get().strip()
        if not text or not self.proc:
            return
        self.input_var.set("")
        self._hint_active = False
        self._history.append(text)
        self._history_pos = -1

        self._user_bubble(text)
        self._disable_input()
        self._set_working(True)

        try:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
        except Exception as e:
            self._append_raw("err_msg", f"Send error: {e}\n")
            self._enable_input()
            self._set_working(False)

    def _send_confirm(self, answer: str):
        self._hide_confirm_buttons()
        self._system_msg(f"You chose: {answer}")

        try:
            self.proc.stdin.write(answer + "\n")
            self.proc.stdin.flush()
        except Exception as e:
            self._append_raw("err_msg", f"Confirm error: {e}\n")

        self._set_working(True)

    def _history_up(self, event=None):
        if not self._history:
            return
        self._history_pos = min(self._history_pos + 1, len(self._history) - 1)
        self.input_var.set(self._history[-(self._history_pos + 1)])
        self._hint_active = False
        self.entry.config(fg=TEXT_HI)

    def _history_down(self, event=None):
        if self._history_pos <= 0:
            self._history_pos = -1
            self.input_var.set("")
            return
        self._history_pos -= 1
        self.input_var.set(self._history[-(self._history_pos + 1)])

    # ── Working state ─────────────────────────────────────────────────────

    # def _set_working(self, state: bool):
    #     self.working = state
    #     if state:
    #         self.thinking_bar.pack(fill="x", side="bottom",
    #                                before=self.root.pack_slaves()[-1])
    #         self.subtitle.config(text="Working…", fg=AMBER)
    #         self._cog_tick()
    #     else:
    #         self.thinking_bar.pack_forget()
    #         self._cog_canvas.delete("all")
    #         self.subtitle.config(text="Your personal AI agent", fg=TEXT_DIM)

    def _set_working(self, state: bool):
        self.working = state
        if state:
            self.thinking_bar.pack(fill="x", side="bottom",
                                before=self.root.pack_slaves()[-1])
            self._cog_tick()
        else:
            self.thinking_bar.pack_forget()
            self._cog_canvas.delete("all")

    def _cog_tick(self):
        if not self.working:
            return
        import math
        c  = self._cog_canvas
        cx, cy = 9, 9          # centre
        R_out  = 8             # outer radius (tip of teeth)
        R_in   = 5             # inner radius (root of teeth)
        R_hub  = 2             # centre hole
        TEETH  = 8
        a      = self._cog_angle

        c.delete("all")

        # Build cog polygon points
        pts = []
        for i in range(TEETH):
            base_angle = math.radians(a + i * 360 / TEETH)
            half_tooth = math.radians(360 / TEETH * 0.3)

            # Four points per tooth: inner-left, outer-left, outer-right, inner-right
            for angle, radius in [
                (base_angle - half_tooth * 1.5, R_in),
                (base_angle - half_tooth * 0.5, R_out),
                (base_angle + half_tooth * 0.5, R_out),
                (base_angle + half_tooth * 1.5, R_in),
            ]:
                pts.append(cx + radius * math.cos(angle))
                pts.append(cy + radius * math.sin(angle))

        c.create_polygon(pts, fill=ACCENT, outline="", smooth=False)

        # Hub hole (draw bg-coloured circle in centre)
        c.create_oval(cx - R_hub, cy - R_hub,
                      cx + R_hub, cy + R_hub,
                      fill=CARD2, outline="")

        self._cog_angle = (self._cog_angle + 6) % 360   # 6° per tick
        self.root.after(40, self._cog_tick)              # ~25fps

    # ── Enable / disable ──────────────────────────────────────────────────

    def _enable_input(self):
        if self._confirming:
            return
        self.entry.config(state="normal")
        self.send_btn.config(state="normal", bg=ACCENT)
        if not self._hint_active:
            self.entry.focus_set()

    def _disable_input(self):
        self.entry.config(state="disabled")
        self.send_btn.config(state="disabled", bg=TEXT_DIM)

    # ── Confirm ───────────────────────────────────────────────────────────

    def _show_confirm_buttons(self):
        self._confirming = True
        self._disable_input()
        self._append_raw("confirm", "  ⚠  Action requires your approval\n")
        self.confirm_frame.pack(fill="x", before=self.root.pack_slaves()[-1])
        self._set_working(False)

    def _hide_confirm_buttons(self):
        self._confirming = False
        self.confirm_frame.pack_forget()
        self._set_working(True)

    # ── Close ─────────────────────────────────────────────────────────────

    def _on_close(self):
        if self.proc:
            try:
                self.proc.stdin.write("exit\n")
                self.proc.stdin.flush()
            except Exception:
                pass
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app  = AgentUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()