import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import random
import subprocess
import tempfile
import os
import shutil
from checker import find_syntax_errors

# Small set of C keywords for highlighting
_C_KEYWORDS = {
    'auto','break','case','char','const','continue','default','do','double','else','enum',
    'extern','float','for','goto','if','inline','int','long','register','restrict','return',
    'short','signed','sizeof','static','struct','switch','typedef','union','unsigned','void',
    'volatile','while','_Bool','_Complex','_Imaginary'
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('C Syntax Checker')
        self.geometry('1000x650')
        self._build_ui()

    def _build_ui(self):
        # Colors for dark theme
        bg = '#0b0f12'  # almost black
        panel = '#0f1720'  # dark panel
        gutter = '#0b1220'
        accent = '#ff8c42'
        text_bg = '#0c0f10'
        text_fg = '#e6eef6'

        self.configure(bg=bg)
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(size=10)
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg, foreground=text_fg)
        style.configure('Accent.TButton', background=accent, foreground='#0b0f12', font=('Segoe UI', 9, 'bold'))
        style.map('Accent.TButton', background=[('active', '#ff7a20')])

        # Toolbar
        top = ttk.Frame(self, padding=(8, 8), style='TFrame')
        top.pack(side='top', fill='x')

        open_btn = ttk.Button(top, text='Open C File', command=self.open_file, style='Accent.TButton')
        open_btn.pack(side='left', padx=6)

        check_btn = ttk.Button(top, text='Check Syntax', command=self.check_syntax, style='Accent.TButton')
        check_btn.pack(side='left', padx=6)

        run_btn = ttk.Button(top, text='Run Code', command=self.run_code, style='Accent.TButton')
        run_btn.pack(side='left', padx=6)

        clear_btn = ttk.Button(top, text='Clear', command=self.clear_all)
        clear_btn.pack(side='left', padx=6)

        sample_btn = ttk.Button(top, text='Insert Sample', command=self.insert_sample)
        sample_btn.pack(side='left', padx=6)

        # Main panes
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=8, pady=(4,8))

        editor_frame = ttk.Frame(paned)
        paned.add(editor_frame, weight=3)
        errors_frame = ttk.Frame(paned)
        paned.add(errors_frame, weight=1)

        # Line numbers + editor
        ln_frame = ttk.Frame(editor_frame)
        ln_frame.pack(fill='both', expand=True)

        # Use the same monospace font for the gutter so numbers align with code lines
        self.ln = tk.Text(ln_frame, width=4, padx=6, takefocus=0, border=0, background=gutter, foreground='#7f8c8d', state='disabled', font=('Consolas', 12))
        self.ln.pack(side='left', fill='y')

        self.editor = tk.Text(ln_frame, wrap='none', font=('Consolas', 12), undo=True, background=text_bg, foreground=text_fg, insertbackground=text_fg)
        self.editor.pack(side='left', fill='both', expand=True)
        self.editor.bind('<KeyRelease>', self._on_edit)
        self.editor.bind('<ButtonRelease>', self._update_cursor)

        # Error/Output panel: use a Notebook with two tabs so Run Code can show program output separately
        notebook = ttk.Notebook(errors_frame)
        notebook.pack(fill='both', expand=True, padx=(4,4), pady=(0,4))
        # keep references so run_code can switch tabs
        self.notebook = notebook

        # Errors tab
        errors_tab = ttk.Frame(notebook)
        notebook.add(errors_tab, text='Errors')
        errors_label = ttk.Label(errors_tab, text='Errors')
        errors_label.pack(anchor='nw')
        self.errors_text = tk.Text(errors_tab, height=15, background=panel, foreground='#ffb3b3', wrap='none', relief='flat')
        self.errors_text.pack(fill='both', expand=True)
        self.errors_text.tag_config('error', foreground='#ff6b6b')
        self.errors_text.tag_config('info', foreground='#9ad1ff')
        self.errors_text.bind('<Button-1>', self._errors_click)

        # Output tab
        output_tab = ttk.Frame(notebook)
        notebook.add(output_tab, text='Output')
        output_label = ttk.Label(output_tab, text='Output')
        output_label.pack(anchor='nw')
        self.output_text = tk.Text(output_tab, height=10, background=panel, foreground='#b8ffb3', wrap='none', relief='flat')
        self.output_text.pack(fill='both', expand=True)
        self.output_text.tag_config('out', foreground='#b8ffb3')
        # store tab frames for selecting
        self.errors_tab = errors_tab
        self.output_tab = output_tab

        # Status bar
        self.status = ttk.Label(self, text='Ready', relief='sunken', anchor='w', background=bg, foreground=text_fg)
        self.status.pack(side='bottom', fill='x')

        # initial lines and highlighting tags
        self._update_line_numbers()
        self.editor.tag_config('kw', foreground='#7ecbff')
        self.editor.tag_config('str', foreground='#ffd479')
        self.editor.tag_config('errline', background='#2a1f1f')

    def insert_sample(self):
        good_samples = [
            '#include <stdio.h>\nint main() { int x = 5; printf("x=%d\\n", x); return 0; }\n',
            '#include <stdio.h>\nvoid greet() { printf("Hello\\n"); }\nint main() { greet(); return 0; }\n'
        ]
        bad_samples = [
            'int main() { int 1x = 5\n char *s = "oops\n }\n',
            '#include <stdio.h>;\nint main() { return 0; }\n',
            '#include <stdio.h>\nint main() { scanf("%d", &x); return 0; }\n'  # missing declaration/use
        ]
        pool = good_samples + bad_samples
        choice = random.choice(pool)
        last = getattr(self, '_last_sample', None)
        attempts = 0
        while choice == last and attempts < 8:
            choice = random.choice(pool)
            attempts += 1
        self._last_sample = choice
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', choice)
        self._update_line_numbers()
        self._apply_highlighting()
        self.status.config(text='Inserted sample (random)')

    def _on_edit(self, event=None):
        self._update_line_numbers()
        self._apply_highlighting()

    def _update_cursor(self, event=None):
        try:
            pos = self.editor.index('insert')
            line, col = pos.split('.')
            self.status.config(text=f'Ln {line}, Col {col}')
        except Exception:
            self.status.config(text='Ready')

    def _apply_highlighting(self):
        self.editor.tag_remove('kw', '1.0', 'end')
        self.editor.tag_remove('str', '1.0', 'end')
        # highlight strings
        idx = '1.0'
        while True:
            pos = self.editor.search('"', idx, stopindex='end')
            if not pos:
                break
            pos2 = self.editor.search('"', f'{pos}+1c', stopindex='end')
            if not pos2:
                line_end = pos.split('.')[0] + '.end'
                self.editor.tag_add('str', pos, line_end)
                break
            self.editor.tag_add('str', pos, f'{pos2}+1c')
            idx = f'{pos2}+1c'
        for kw in _C_KEYWORDS:
            start = '1.0'
            while True:
                pos = self.editor.search(rf'\b{kw}\b', start, stopindex='end', regexp=True)
                if not pos:
                    break
                end = f'{pos}+{len(kw)}c'
                self.editor.tag_add('kw', pos, end)
                start = end

    def _update_line_numbers(self):
        lines = int(self.editor.index('end-1c').split('.')[0])
        ln_text = '\n'.join(str(i) for i in range(1, lines)) + ('\n' if lines > 1 else '')
        self.ln.config(state='normal')
        self.ln.delete('1.0', 'end')
        self.ln.insert('1.0', ln_text)
        self.ln.config(state='disabled')

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[('C files','*.c;*.h;*.cpp'), ('All files','*.*')])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.editor.delete('1.0', 'end')
            self.editor.insert('1.0', text)
            self.title(f'C Syntax Checker - {path}')
            self._update_line_numbers()
        except Exception as e:
            messagebox.showerror('Error', f'Could not open file: {e}')

    def check_syntax(self):
        src = self.editor.get('1.0', 'end').strip()
        if not src:
            messagebox.showwarning('Empty input', 'Please enter C code before checking.')
            return
        errors = find_syntax_errors(src)
        self.errors_text.config(state='normal')
        self.errors_text.delete('1.0', 'end')
        if not errors:
            self.errors_text.insert('end', 'No syntax issues detected.\n', 'info')
            self.status.config(text='No issues found')
            self.errors_text.config(state='disabled')
            return
        for err in errors:
            line = err.get('line') if err.get('line') is not None else '-'
            text = f'Line {line}: {err.get("type")}: {err.get("message")}\n'
            tag = 'error' if 'error' in err.get('type','').lower() or 'missing' in err.get('type','').lower() else 'info'
            self.errors_text.insert('end', text, tag)
        self.errors_text.config(state='disabled')
        self.status.config(text=f'{len(errors)} issue(s) found')

    def clear_all(self):
        # Clear editor
        self.editor.delete('1.0', 'end')
        # Reset line numbers and highlighting
        self._update_line_numbers()
        # Clear errors tab
        self.errors_text.config(state='normal')
        self.errors_text.delete('1.0', 'end')
        self.errors_text.config(state='disabled')
        # Clear output tab if present
        if hasattr(self, 'output_text'):
            self.output_text.config(state='normal')
            self.output_text.delete('1.0', 'end')
            self.output_text.config(state='disabled')
        # Reset status and window title
        try:
            self.status.config(text='Ready')
        except Exception:
            pass
        try:
            self.title('C Syntax Checker')
        except Exception:
            pass
        # forget last sample so Insert Sample can re-pick
        if hasattr(self, '_last_sample'):
            delattr(self, '_last_sample') if hasattr(self, '_last_sample') else None
        # focus editor
        try:
            self.editor.focus()
        except Exception:
            pass

    def _errors_click(self, event):
        idx = self.errors_text.index(f'@{event.x},{event.y}')
        line_no = int(idx.split('.')[0])
        line_text = self.errors_text.get(f'{line_no}.0', f'{line_no}.end')
        if line_text.lower().startswith('line'):
            parts = line_text.split(':')
            if parts:
                try:
                    num = int(parts[0].strip().split()[1])
                    self.editor.mark_set('insert', f'{num}.0')
                    self.editor.see(f'{num}.0')
                    self.editor.focus()
                except Exception:
                    pass

    def run_code(self):
        """Attempt to compile & run the current C code using gcc/clang if available.
        If compiler is not available, show a helpful message.
        """
        src = self.editor.get('1.0', 'end').strip()
        if not src:
            messagebox.showwarning('Empty input', 'Please enter C code before running.')
            return
        # first run our syntax checks
        errors = find_syntax_errors(src)
        if errors:
            self.errors_text.config(state='normal')
            self.errors_text.delete('1.0', 'end')
            for err in errors:
                line = err.get('line') if err.get('line') is not None else '-'
                text = f'Line {line}: {err.get("type")}: {err.get("message")}\n'
                self.errors_text.insert('end', text, 'error')
            self.errors_text.config(state='disabled')
            self.status.config(text=f'{len(errors)} issue(s) found — fix before running')
            return

        # look for gcc/clang
        comp = shutil.which('gcc') or shutil.which('clang')
        if not comp:
            messagebox.showinfo('No compiler', 'gcc/clang not found in PATH. Only syntax checking is available.')
            return

        # write to temp file
        with tempfile.TemporaryDirectory() as td:
            cpath = os.path.join(td, 'prog.c')
            exe = os.path.join(td, 'prog.exe' if os.name == 'nt' else 'prog')
            with open(cpath, 'w', encoding='utf-8') as f:
                f.write(src)
            # compile
            try:
                proc = subprocess.run([comp, cpath, '-o', exe], capture_output=True, text=True, timeout=10)
            except Exception as e:
                messagebox.showerror('Error', f'Compilation failed: {e}')
                return
            if proc.returncode != 0:
                # show compiler stderr in Errors tab and switch to it
                self.errors_text.config(state='normal')
                self.errors_text.delete('1.0', 'end')
                self.errors_text.insert('end', proc.stderr or proc.stdout, 'error')
                self.errors_text.config(state='disabled')
                self.status.config(text='Compilation failed')
                try:
                    self.notebook.select(self.errors_tab)
                except Exception:
                    pass
                return
            # run the binary
            try:
                runp = subprocess.run([exe], capture_output=True, text=True, timeout=5)
            except Exception as e:
                messagebox.showerror('Error', f'Program execution failed: {e}')
                return
            out = runp.stdout or ''
            errout = runp.stderr or ''
            # write stdout to Output tab, stderr to Errors tab; switch to Output when program ran
            self.output_text.config(state='normal')
            self.output_text.delete('1.0', 'end')
            if out:
                self.output_text.insert('end', out, 'out')
            if not out:
                self.output_text.insert('end', 'Program finished with no output.\n', 'out')
            self.output_text.config(state='disabled')

            self.errors_text.config(state='normal')
            self.errors_text.delete('1.0', 'end')
            if errout:
                self.errors_text.insert('end', errout, 'error')
            self.errors_text.config(state='disabled')

            self.status.config(text='Program ran')
            try:
                self.notebook.select(self.output_tab)
            except Exception:
                pass


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
