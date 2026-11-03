import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from PIL import Image, ImageOps

TARGET_RATIO = 9 / 4
RATIO_TOLERANCE = 0.001  # 0,1 %
JPEG_QUALITY = 95

selected_file = None


def choose_photo():
    global selected_file

    filename = filedialog.askopenfilename(
        title="Panoramafoto auswählen",
        filetypes=[("JPEG-Bilder", "*.jpg *.jpeg"), ("Alle Dateien", "*.*")]
    )

    if filename:
        selected_file = Path(filename)
        file_label.config(text=selected_file.name)
        split_button.config(state=tk.NORMAL)
        status_label.config(text="Foto ausgewählt. Du kannst es jetzt aufteilen.")


def split_photo():
    if selected_file is None:
        return

    try:
        with Image.open(selected_file) as source:
            # Berücksichtigt die EXIF-Drehung, falls vorhanden.
            image = ImageOps.exif_transpose(source)

            width, height = image.size
            actual_ratio = width / height
            deviation = abs(actual_ratio / TARGET_RATIO - 1)

            if deviation > RATIO_TOLERANCE:
                messagebox.showerror(
                    "Falsches Seitenverhältnis",
                    f"Das Foto hat {width} × {height} Pixel.\n"
                    f"Das Seitenverhältnis ist {actual_ratio:.5f}, "
                    f"erwartet wird 2,25 (9:4).\n\n"
                    "Bitte schneide das Foto in Lightroom auf 9:4 zu "
                    "und exportiere es erneut."
                )
                return

            if width % 3 != 0:
                messagebox.showerror(
                    "Bildbreite nicht durch 3 teilbar",
                    f"Das Foto ist {width} Pixel breit.\n"
                    "Damit alle drei Teile exakt gleich breit sind, "
                    "muss die Bildbreite durch 3 teilbar sein.\n\n"
                    "Bitte passe die Exportgröße in Lightroom an."
                )
                return

            # JPEG kann keine Transparenz speichern.
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            elif image.mode == "L":
                image = image.convert("RGB")

            part_width = width // 3
            export_folder = selected_file.parent / "Export"
            export_folder.mkdir(exist_ok=True)

            parts = [
                ("links", 0, part_width),
                ("mitte", part_width, 2 * part_width),
                ("rechts", 2 * part_width, width),
            ]

            for suffix, left, right in parts:
                part = image.crop((left, 0, right, height))
                output_file = export_folder / f"{selected_file.stem}_{suffix}.jpg"
                save_options = {
                    "format": "JPEG",
                    "quality": JPEG_QUALITY,
                    "optimize": True,
                }

                # Falls vorhanden, eingebettetes Farbprofil erhalten.
                icc_profile = image.info.get("icc_profile")
                if icc_profile:
                    save_options["icc_profile"] = icc_profile

                part.save(output_file, **save_options)

            messagebox.showinfo(
                "Fertig",
                "Das Panorama wurde erfolgreich aufgeteilt.\n\n"
                f"Bildgröße je Teil: {part_width} × {height} Pixel\n"
                f"Gespeichert in:\n{export_folder}"
            )
            status_label.config(text=f"Fertig! Dateien liegen in: {export_folder}")

    except Exception as error:
        messagebox.showerror(
            "Fehler beim Verarbeiten",
            f"Das Foto konnte nicht verarbeitet werden.\n\n{error}"
        )


root = tk.Tk()
root.title("Instagram Panorama Splitter")
root.resizable(False, False)
root.geometry("440x230")

main = tk.Frame(root, padx=20, pady=18)
main.pack(fill="both", expand=True)

title = tk.Label(
    main,
    text="Instagram Panorama Splitter",
    font=("Segoe UI", 15, "bold")
)
title.pack(anchor="w")

description = tk.Label(
    main,
    text="Teilt ein 9:4-Foto in drei gleich große JPEG-Bilder.",
    font=("Segoe UI", 9)
)
description.pack(anchor="w", pady=(4, 14))

choose_button = tk.Button(
    main,
    text="1. Foto auswählen",
    command=choose_photo,
    width=22,
    height=2
)
choose_button.pack(anchor="w")

file_label = tk.Label(
    main,
    text="Noch kein Foto ausgewählt",
    font=("Segoe UI", 9),
    wraplength=390,
    justify="left"
)
file_label.pack(anchor="w", pady=(8, 12))

split_button = tk.Button(
    main,
    text="2. Aufteilen",
    command=split_photo,
    width=22,
    height=2,
    state=tk.DISABLED
)
split_button.pack(anchor="w")

status_label = tk.Label(
    main,
    text="",
    font=("Segoe UI", 8),
    wraplength=390,
    justify="left",
    fg="gray"
)
status_label.pack(anchor="w", pady=(10, 0))

root.mainloop()
