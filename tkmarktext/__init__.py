#region Imports


import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


#endregion
#region Shared Logic


__all__ = ["TextPanel", "TextWindow", "_Mixin"]


class _Mixin:
    """Helpers to render text into a Tk Text/ScrolledText widget."""
    def _setup_text_widgets(self, footer: Optional[Union[str, Callable[[Any], Any]]] = None, include_scrollbar: bool = True) -> None:
        """Create textbox (optionally with scrollbar) and footer."""
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(expand=True, fill="both")
        if include_scrollbar:
            self.textbox = scrolledtext.ScrolledText(self.content_frame, wrap="word", height=1, padx=6, pady=2, insertbackground="white")
        else:
            self.textbox = tk.Text(self.content_frame, wrap="word", height=1, padx=6, pady=2, insertbackground="white")
        self.textbox.pack(expand=True, fill='both')
        self.textbox.config(state='disabled')
        self.textbox.bind("<FocusOut>", lambda e: self.textbox.tag_remove("sel", "1.0", "end"), add="+")
        self._configure_text_tags()
        self.set_font(color="#0B0B16")
        self.current_text = None
        self.current_rich_text = True
        self.footer = footer
        self.footer_widget = None
        if self.footer:
            self._create_footer()
        self.context_menu = tk.Menu(self.textbox, tearoff=0)
        self.context_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self._copy_selection)
        self.textbox.bind("<Button-3>", self._show_context_menu, add="+")


    def _configure_text_tags(self):
        """Configure text tags for headings, styles, and justification."""
        tag_fonts = {
            "#heading":     ("", 16, "bold"),
            "##heading":    ("", 14, "bold"),
            "###heading":   ("", 12, "bold"),
            "content":      ("", 10),
            "bold":         ("", 10, "bold"),
            "italic":       ("", 10, "italic"),
            "bolditalic":   ("", 10, "bold", "italic"),
        }
        for tag, font_spec in tag_fonts.items():
            self.textbox.tag_config(tag, font=font_spec)
        self.textbox.tag_config("justify_left", justify='left')
        self.textbox.tag_config("justify_center", justify='center')
        self.textbox.tag_config("justify_right", justify='right')


    def _show_context_menu(self, event: tk.Event) -> str:
        """Show context menu at mouse position, enabling Copy if selection exists."""
        try:
            has_selection = bool(self.textbox.tag_ranges("sel"))
            if has_selection:
                self.context_menu.entryconfigure(0, state="normal")
            else:
                self.context_menu.entryconfigure(0, state="disabled")
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                self.context_menu.grab_release()
            except Exception:
                pass
        return "break"


    def _create_footer(self) -> None:
        """Create footer widget from string or callable."""
        if self.footer_widget or not self.footer:
            return
        elif callable(self.footer):
            self.footer_widget = self.footer(self)
            if self.footer_widget is not None:
                self.footer_widget.pack(side="bottom", fill="x")
        else:
            self.footer_widget = ttk.Label(self, text=str(self.footer), font=("", 10))
            self.footer_widget.pack(side="bottom", fill="x")


#endregion
#region API / Config


    def configure(self, cnf: Optional[Union[Dict[str, Any], Any]] = None, **kwargs: Any) -> Any:
        """Extend configure to handle custom options."""
        custom_keys = ("text", "rich_text", "footer", "include_scrollbar")
        kwargs = dict(kwargs)
        cnf_payload = dict(cnf) if isinstance(cnf, dict) else cnf
        custom_options = {}
        if isinstance(cnf_payload, dict):
            for key in custom_keys:
                if key in cnf_payload:
                    custom_options[key] = cnf_payload.pop(key)
        for key in custom_keys:
            if key in kwargs:
                custom_options[key] = kwargs.pop(key)
        if isinstance(cnf, dict):
            result = super().configure(cnf_payload, **kwargs)
        elif cnf is None:
            result = super().configure(**kwargs)
        else:
            result = super().configure(cnf, **kwargs)
        if custom_options:
            widget_ready = hasattr(self, "textbox")
            if widget_ready:
                if ("footer" in custom_options) or ("include_scrollbar" in custom_options):
                    self.content_frame.destroy()
                    footer_arg = custom_options.get("footer", None)
                    include_arg = custom_options.get("include_scrollbar", True)
                    self._setup_text_widgets(footer=footer_arg, include_scrollbar=include_arg)
                if ("text" in custom_options) or ("rich_text" in custom_options):
                    text = custom_options.get("text", getattr(self, "_current_text", None))
                    rich_text = custom_options.get("rich_text", getattr(self, "_current_rich_text", True))
                    self._update_text(text, rich_text)
        return result


    def config(self, cnf: Optional[Union[Dict[str, Any], Any]] = None, **kwargs: Any) -> Any:
        """Alias for configure."""
        return self.configure(cnf, **kwargs)


    def set_text(self, text: Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]] = None, rich_text: bool = True) -> None:
        """Update displayed text."""
        self._update_text(text, rich_text)


    def set_font(self, family: Optional[str] = None, color: Optional[str] = None) -> None:
        """Set font family and color for all text tags."""
        tags = ["#heading", "##heading", "###heading", "bold", "italic", "bolditalic", "content"]
        for tag in tags:
            current_font = self.textbox.tag_cget(tag, "font")
            font_parts = list(self.textbox.tk.splitlist(current_font)) if current_font else ["", 10]
            if family:
                font_parts[0] = family
            font_tuple = tuple(font_parts)
            self.textbox.tag_config(tag, font=font_tuple)
            if color:
                self.textbox.tag_config(tag, foreground=color, selectbackground="#0078d7", selectforeground="white")


#endregion
#region Content


    def _update_text(self, text: Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]] = None, rich_text: bool = True) -> None:
        """Render text into the textbox."""
        self.textbox.config(state='normal')
        self.textbox.delete("1.0", "end")
        stripped_text = self._strip_leading_whitespace(text)
        if stripped_text is None:
            self.textbox.insert("end", "No text available")
            self.textbox.config(state='disabled')
            self.current_text = None
            self.current_rich_text = rich_text
            return
        if rich_text:
            if not isinstance(stripped_text, str):
                self.textbox.insert("end", "Error: Rich text mode requires a string input.")
            else:
                self._insert_rich_text(stripped_text)
        else:
            self._insert_simple_text(stripped_text)
        self.textbox.config(state='disabled')
        self.current_text = text
        self.current_rich_text = rich_text


    def _strip_leading_whitespace(self, text: Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]]) -> Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]]:
        """Strip leading whitespace from strings, dict values, and list items."""
        if text is None:
            return None
        if isinstance(text, str):
            return text.lstrip()
        elif isinstance(text, dict):
            return {k.lstrip() if isinstance(k, str) else k: v.lstrip() if isinstance(v, str) else v for k, v in text.items()}
        elif isinstance(text, (list, tuple)):
            return type(text)(item.lstrip() if isinstance(item, str) else item for item in text)
        return text


    def _insert_simple_text(self, text: Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]) -> None:
        """Insert text without formatting."""
        try:
            out = ""
            if isinstance(text, dict):
                for heading, content in text.items():
                    out += f"{heading}\n{content}\n\n"
            elif isinstance(text, list):
                for item in text:
                    out += f"{str(item)}\n"
            else:
                out = str(text)
            self.textbox.insert("end", out)
        except Exception as e:
            self.textbox.insert("end", f"Error: {str(e)}")


    def _get_tags_with_justify(self, base_tags: Union[str, Tuple[str, ...]], justify_type: Optional[str]) -> Tuple[str, ...]:
        """Return tag tuple with optional justification tag."""
        if justify_type:
            if isinstance(base_tags, tuple):
                return base_tags + (justify_type,)
            else:
                return (base_tags, justify_type)
        return base_tags if isinstance(base_tags, tuple) else (base_tags,)


    def _insert_rich_text(self, text: str) -> None:
        """Insert text using Markdown-like rules and justification tags."""
        try:
            blocks = self._parse_justify_blocks(text)
            for justify_type, block_text in blocks:
                lines = block_text.splitlines()
                blank_line_pending = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("### "):
                        heading_text = stripped[4:]
                        tags = self._get_tags_with_justify("###heading", justify_type)
                        self.textbox.insert("end", heading_text + "\n", tags)
                        blank_line_pending = False
                    elif stripped.startswith("## "):
                        heading_text = stripped[3:]
                        tags = self._get_tags_with_justify("##heading", justify_type)
                        self.textbox.insert("end", heading_text + "\n", tags)
                        blank_line_pending = False
                    elif stripped.startswith("# "):
                        heading_text = stripped[2:]
                        tags = self._get_tags_with_justify("#heading", justify_type)
                        self.textbox.insert("end", heading_text + "\n", tags)
                        blank_line_pending = False
                    elif stripped:
                        formatted_parts = self._parse_style(line)
                        for tag_name, txt in formatted_parts:
                            tags = self._get_tags_with_justify(tag_name, justify_type)
                            self.textbox.insert("end", txt, tags)
                        self.textbox.insert("end", "\n")
                        blank_line_pending = False
                    else:
                        if not blank_line_pending:
                            self.textbox.insert("end", "\n")
                            blank_line_pending = True
        except Exception as e:
            self.textbox.insert("end", f"Error: {str(e)}")


    def _copy_selection(self) -> None:
        """Copy selected text to clipboard."""
        try:
            if not self.textbox.tag_ranges("sel"):
                return
            selected = self.textbox.get("sel.first", "sel.last")
            self.textbox.clipboard_clear()
            self.textbox.clipboard_append(selected)
        except tk.TclError:
            pass


#endregion
#region Parse / Format


    def _parse_justify_blocks(self, text: str) -> List[Tuple[Optional[str], str]]:
        """Return (justify_tag_or_None, text_segment) tuples for justify blocks."""
        import re
        blocks = []
        pattern = r'\[justify:(left|center|right)\](.*?)\[/justify\]'
        last_end = 0
        for match in re.finditer(pattern, text, re.DOTALL):
            if match.start() > last_end:
                pre_text = text[last_end:match.start()]
                if pre_text:
                    blocks.append((None, pre_text))
            alignment = match.group(1)
            content = match.group(2)
            justify_tag = f"justify_{alignment}"
            if content:
                blocks.append((justify_tag, content))
            last_end = match.end()
        if last_end < len(text):
            post_text = text[last_end:]
            if post_text:
                blocks.append((None, post_text))
        if not blocks:
            blocks.append((None, text))
        blocks = [(jt, seg) for jt, seg in blocks if seg and seg.strip() != ""]
        return blocks


    def _parse_style(self, text: str) -> List[Tuple[Union[str, Tuple[str, ...]], str]]:
        """Parse bold/italic markers, matching paired markers on the same line."""
        final_parts = []
        bi_segments = self._find_marker_pairs(text, "***")
        for is_bi, segment in bi_segments:
            if is_bi:
                final_parts.append(("bolditalic", segment))
                continue
            bold_segments = self._find_marker_pairs(segment, "**")
            for is_bold, seg in bold_segments:
                if is_bold:
                    final_parts.append(("bold", seg))
                    continue
                italic_segments = self._find_marker_pairs(seg, "*")
                for is_italic, sub_segment in italic_segments:
                    if sub_segment:
                        tag = "italic" if is_italic else "content"
                        final_parts.append((tag, sub_segment))
        return final_parts if final_parts else [('content', text)]


    def _find_marker_pairs(self, text: str, marker: str) -> List[Tuple[bool, str]]:
        """Find paired markers and return (is_marked, segment) tuples."""
        if marker not in text:
            return [(False, text)]
        marker_len = len(marker)
        result = []
        pos = 0
        while pos < len(text):
            start = text.find(marker, pos)
            if start == -1:
                if pos < len(text):
                    result.append((False, text[pos:]))
                break
            if start > pos:
                result.append((False, text[pos:start]))
            close = text.find(marker, start + marker_len)
            if close == -1:
                result.append((False, text[start:start + marker_len]))
                pos = start + marker_len
                continue
            segment_between = text[start + marker_len:close]
            if '\n' in segment_between:
                result.append((False, text[start:start + marker_len]))
                pos = start + marker_len
                continue
            if segment_between:
                result.append((True, segment_between))
            pos = close + marker_len
        return result if result else [(False, text)]


#endregion
#region TextWindow


class TextWindow(_Mixin, tk.Toplevel):
    """Toplevel window for displaying formatted or plain text."""
    def __init__(self, master: Optional[Any] = None, title: Optional[str] = "Text", geometry: Optional[str] = "400x700", text: Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]] = None, rich_text: bool = True, footer: Optional[Union[str, Callable[[Any], Any]]] = "", include_scrollbar: bool = True) -> None:
        """Initialize TextWindow with configurable parameters."""
        super().__init__(master=master)
        self.title(title if title is not None else "Text")
        self.minsize(200, 200)
        if geometry is not None:
            self.geometry(geometry)
        self.bind("<Escape>", self.close_window, add="+")
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self._setup_widgets(footer=footer, include_scrollbar=include_scrollbar)
        if text is not None:
            self.configure(text=text, rich_text=rich_text)
        self.withdraw()


    def _setup_widgets(self, footer: Optional[Union[str, Callable[[Any], Any]]] = "", include_scrollbar: bool = True) -> None:
        """Set up window widgets."""
        self._setup_text_widgets(footer=footer, include_scrollbar=include_scrollbar)


    def open_window(self, title: Optional[str] = None, geometry: Optional[str] = None, text: Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]] = None, rich_text: bool = True, include_scrollbar: bool = True) -> None:
        """Show window and update title, geometry, and content."""
        self._update_window(title, geometry)
        self.configure(text=text, rich_text=rich_text, include_scrollbar=include_scrollbar)
        self.deiconify()
        self._center_window()
        self.lift()


    def _update_window(self, title: Optional[str] = None, geometry: Optional[str] = None) -> None:
        """Update window title and geometry."""
        if title is not None:
            self.title(title)
        if geometry is not None:
            self.geometry(geometry)


    def _center_window(self) -> None:
        """Center window within master, not exceeding master's size."""
        if not self.master:
            return
        self.update_idletasks()
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        target_width = min(win_width, master_width)
        target_height = min(win_height, master_height)
        x = master_x + (master_width - target_width) // 2
        y = master_y + (master_height - target_height) // 2
        self.geometry(f"{target_width}x{target_height}+{x}+{y}")


    def close_window(self, event: Optional[Any] = None) -> None:
        """Hide the window."""
        self.withdraw()


#endregion
#region TextPanel


class TextPanel(_Mixin, ttk.Frame):
    """Embeddable panel for displaying formatted or plain text."""
    def __init__(self, master: Optional[Any] = None, text: Optional[Union[str, Dict[Any, Any], List[Any], Tuple[Any, ...]]] = None, rich_text: bool = True, footer: Optional[Union[str, Callable[[Any], Any]]] = None, include_scrollbar: bool = True, **kwargs: Any) -> None:
        """Initialize TextPanel."""
        kwargs = dict(kwargs)
        style = kwargs.pop("style", None)
        background = kwargs.pop("background", kwargs.pop("bg", None))
        init_kwargs = kwargs
        if style is not None:
            init_kwargs["style"] = style
        super().__init__(master=master, **init_kwargs)
        if background is not None:
            style_name = style or f"TextPanel{ id(self) }.TFrame"
            ttk.Style().configure(style_name, background=background)
            self.configure(style=style_name)
        self._setup_text_widgets(footer=footer, include_scrollbar=include_scrollbar)
        if text is not None:
            self.configure(text=text, rich_text=rich_text)
        else:
            self.textbox.config(state='disabled')


#endregion
