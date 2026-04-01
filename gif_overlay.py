import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os


class GifOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Overlay")

        # ── Window setup ───────────────────────────────────────────────
        self.root.overrideredirect(True)           # no title bar/borders
        self.root.wm_attributes("-topmost", True)  # always on top
        self.root.configure(bg="#1a1a1a")

        # ── State ──────────────────────────────────────────────────────
        self.frames = []
        self.delays = []
        self.current_frame = 0
        self.after_id = None
        self.gif_path = None
        self.size = 200

        # ── UI ─────────────────────────────────────────────────────────
        self.label = tk.Label(self.root, bg="#1a1a1a", cursor="fleur")
        self.label.pack()

        # Drag
        self.label.bind("<ButtonPress-1>", self._drag_start)
        self.label.bind("<B1-Motion>",     self._drag_motion)
        self.label.bind("<Button-3>",      self._show_menu)

        # Context menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Open GIF",         command=self.open_gif)
        self.menu.add_command(label="Open GIF folder",  command=self.open_folder)
        self.menu.add_separator()

        size_menu = tk.Menu(self.menu, tearoff=0)
        for s in [100, 150, 200, 250, 300]:
            size_menu.add_command(label=f"{s} x {s} px",
                                  command=lambda s=s: self.set_size(s))
        self.menu.add_cascade(label="Size", menu=size_menu)

        alpha_menu = tk.Menu(self.menu, tearoff=0)
        for label, val in [("100%", 1.0), ("80%", 0.8), ("60%", 0.6), ("40%", 0.4)]:
            alpha_menu.add_command(label=label,
                                   command=lambda v=val: self.root.wm_attributes("-alpha", v))
        self.menu.add_cascade(label="Opacity", menu=alpha_menu)

        corner_menu = tk.Menu(self.menu, tearoff=0)
        for label, corner in [("Top-left",     "topleft"),
                               ("Top-right",    "topright"),
                               ("Bottom-left",  "bottomleft"),
                               ("Bottom-right", "bottomright")]:
            corner_menu.add_command(label=label,
                                    command=lambda c=corner: self.snap_to_corner(c))
        self.menu.add_cascade(label="Snap to corner", menu=corner_menu)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.root.destroy)

        # ── Start in safe position, then ask for GIF ───────────────────
        self.root.geometry(f"{self.size}x{self.size}+100+100")
        self.root.after(200, self._prompt_on_start)

    # ── Startup ────────────────────────────────────────────────────────

    def _prompt_on_start(self):
        self.open_gif()

    # ── GIF loading ────────────────────────────────────────────────────

    def open_gif(self):
        path = filedialog.askopenfilename(
            title="Choose a GIF",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
        )
        if path:
            self.load_gif(path)

    def open_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder with GIFs")
        if not folder:
            return
        gifs = [os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith(".gif")]
        if not gifs:
            messagebox.showinfo("No GIFs", "No .gif files found in that folder.")
            return
        self._folder_picker(gifs)

    def _folder_picker(self, gifs):
        win = tk.Toplevel(self.root)
        win.title("Pick a GIF")
        win.wm_attributes("-topmost", True)
        tk.Label(win, text="Select a GIF:", pady=8).pack()
        lb = tk.Listbox(win, width=50, height=15)
        lb.pack(padx=10, pady=4)
        for g in gifs:
            lb.insert(tk.END, os.path.basename(g))
        def pick():
            sel = lb.curselection()
            if sel:
                self.load_gif(gifs[sel[0]])
                win.destroy()
        tk.Button(win, text="Load", command=pick).pack(pady=8)

    def load_gif(self, path):
        print(f"[gif_overlay] Loading: {path}")

        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        try:
            img = Image.open(path)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file:\n{e}")
            return

        self.gif_path = path
        self.frames = []
        self.delays = []

        frame_count = 0
        try:
            while True:
                frame = img.copy().convert("RGBA")
                frame.thumbnail((self.size, self.size), Image.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frame))
                delay = img.info.get("duration", 100)
                self.delays.append(max(delay, 20))
                frame_count += 1
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        print(f"[gif_overlay] Loaded {frame_count} frames")

        if not self.frames:
            messagebox.showerror("Error", "No frames found in GIF.")
            return

        # Resize window to match actual frame size
        fw = self.frames[0].width()
        fh = self.frames[0].height()
        print(f"[gif_overlay] Frame size: {fw}x{fh}")

        self.root.geometry(f"{fw}x{fh}")
        self.root.update_idletasks()

        # Snap to bottom-right after we know the real size
        self.snap_to_corner("bottomright")

        self.current_frame = 0
        self._animate()

    def _animate(self):
        if not self.frames:
            return
        frame = self.frames[self.current_frame]
        self.label.config(image=frame, width=frame.width(), height=frame.height())
        delay = self.delays[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.after_id = self.root.after(delay, self._animate)

    # ── Resize ─────────────────────────────────────────────────────────

    def set_size(self, size):
        self.size = size
        if self.gif_path:
            self.load_gif(self.gif_path)

    # ── Positioning ────────────────────────────────────────────────────

    def snap_to_corner(self, corner):
        self.root.update_idletasks()
        sw  = self.root.winfo_screenwidth()
        sh  = self.root.winfo_screenheight()
        w   = self.root.winfo_width()
        h   = self.root.winfo_height()
        pad = 10
        coords = {
            "topleft":     (pad,        pad),
            "topright":    (sw-w-pad,   pad),
            "bottomleft":  (pad,        sh-h-pad),
            "bottomright": (sw-w-pad,   sh-h-pad),
        }
        x, y = coords.get(corner, (pad, pad))
        self.root.geometry(f"+{x}+{y}")
        print(f"[gif_overlay] Snapped to {corner} at ({x}, {y})")

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ── Context menu ───────────────────────────────────────────────────

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()


def main():
    root = tk.Tk()
    app = GifOverlay(root)
    root.mainloop()


if __name__ == "__main__":
    main()