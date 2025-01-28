import os
import torch
import whisper
import pysrt
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class VideoMetadata:
    width: int
    height: int
    fps: float

class SubtitleEditor:
    def __init__(self, subtitles: pysrt.SubRipFile, callback_after_save):
        """
        Interface d'édition des sous-titres avec visualisation en tableau
        """
        self.subtitles = subtitles
        self.modified = False
        self.callback_after_save = callback_after_save
        self.setup_gui()


    def setup_gui(self):
        """Configuration de l'interface graphique"""
        self.root = tk.Tk()
        self.root.title("Éditeur de sous-titres")
        self.root.geometry("1200x800")
        
        self.create_menu()
        self.create_main_frame()
        self.create_buttons()
        self.populate_tree()
        self.bind_events()

    def create_menu(self):
        """Création de la barre de menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Sauvegarder", command=self.save_subtitles)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.finish)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Modifier la sélection", command=self.edit_subtitle)
        edit_menu.add_command(label="Supprimer la sélection", command=self.delete_subtitle)

    def create_main_frame(self):
        """Création du frame principal avec le tableau"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configuration du tableau
        columns = ('Index', 'Début', 'Fin', 'Texte')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings')
        
        for col, width in zip(columns, [50, 100, 100, 900]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        # Scrollbars
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Placement des éléments
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

    def create_buttons(self):
        """Création des boutons d'action"""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        buttons = [
            ("Ajouter", self.add_subtitle),
            ("Modifier", self.edit_subtitle),
            ("Supprimer", self.delete_subtitle),
            ("Sauvegarder", self.save_subtitles),
            ("Terminer", self.finish)
        ]

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)

    def bind_events(self):
        """Configuration des événements"""
        self.tree.bind('<Double-1>', lambda e: self.edit_subtitle())
        self.tree.bind('<Delete>', lambda e: self.delete_subtitle())

    def populate_tree(self):
        """Remplissage du tableau avec les sous-titres"""
        for sub in self.subtitles:
            self.tree.insert('', 'end', values=(
                sub.index,
                str(sub.start),
                str(sub.end),
                sub.text.replace('\n', ' ')
            ))

    def add_subtitle(self):
        """Ajout d'un nouveau sous-titre"""
        index = len(self.subtitles) + 1
        last_end = self.subtitles[-1].end if self.subtitles else pysrt.SubRipTime(0, 0, 0, 0)
        
        edit_window = self.create_edit_window(
            title=f"Ajouter un sous-titre #{index}",
            text="",
            start=last_end,
            end=last_end + pysrt.SubRipTime(0, 0, 2)
        )
        
        def save_new():
            try:
                text = edit_window.text_entry.get('1.0', tk.END).strip()
                start = pysrt.SubRipTime.from_string(edit_window.start_entry.get())
                end = pysrt.SubRipTime.from_string(edit_window.end_entry.get())
                
                sub = pysrt.SubRipItem(index, start, end, text)
                self.subtitles.append(sub)
                
                self.tree.insert('', 'end', values=(index, str(start), str(end), text))
                self.modified = True
                edit_window.destroy()
                
            except ValueError as e:
                messagebox.showerror("Erreur", f"Format de temps invalide: {str(e)}")
        
        edit_window.save_button.config(command=save_new)

    def edit_subtitle(self):
        """Modification d'un sous-titre existant"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Attention", "Veuillez sélectionner un sous-titre à modifier.")
            return

        item = selected_item[0]
        index = int(self.tree.item(item)['values'][0]) - 1
        sub = self.subtitles[index]
        
        edit_window = self.create_edit_window(
            title=f"Modifier le sous-titre #{sub.index}",
            text=sub.text,
            start=sub.start,
            end=sub.end
        )
        
        def save_changes():
            try:
                sub.text = edit_window.text_entry.get('1.0', tk.END).strip()
                sub.start = pysrt.SubRipTime.from_string(edit_window.start_entry.get())
                sub.end = pysrt.SubRipTime.from_string(edit_window.end_entry.get())
                
                self.tree.item(item, values=(
                    sub.index,
                    str(sub.start),
                    str(sub.end),
                    sub.text.replace('\n', ' ')
                ))
                
                self.modified = True
                edit_window.destroy()
                
            except ValueError as e:
                messagebox.showerror("Erreur", f"Format de temps invalide: {str(e)}")
        
        edit_window.save_button.config(command=save_changes)

    def create_edit_window(self, title: str, text: str, start: pysrt.SubRipTime, end: pysrt.SubRipTime):
        """Création d'une fenêtre d'édition de sous-titre"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title(title)
        edit_window.geometry("600x400")
        
        # Zone de texte
        ttk.Label(edit_window, text="Texte:").pack(pady=5)
        edit_window.text_entry = scrolledtext.ScrolledText(edit_window, height=5)
        edit_window.text_entry.insert('1.0', text)
        edit_window.text_entry.pack(padx=5, pady=5, fill=tk.X)
        
        # Champs de temps
        time_frame = ttk.Frame(edit_window)
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(time_frame, text="Début:").grid(row=0, column=0, padx=5)
        edit_window.start_entry = ttk.Entry(time_frame)
        edit_window.start_entry.insert(0, str(start))
        edit_window.start_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(time_frame, text="Fin:").grid(row=0, column=2, padx=5)
        edit_window.end_entry = ttk.Entry(time_frame)
        edit_window.end_entry.insert(0, str(end))
        edit_window.end_entry.grid(row=0, column=3, padx=5)
        
        # Bouton de sauvegarde
        edit_window.save_button = ttk.Button(edit_window, text="Sauvegarder")
        edit_window.save_button.pack(pady=10)
        
        return edit_window

    def delete_subtitle(self):
        """Suppression d'un sous-titre"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Attention", "Veuillez sélectionner un sous-titre à supprimer.")
            return

        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce sous-titre ?"):
            item = selected_item[0]
            index = int(self.tree.item(item)['values'][0]) - 1
            del self.subtitles[index]
            self.tree.delete(item)
            self.modified = True
            
            # Mise à jour des index
            for i, sub in enumerate(self.subtitles, 1):
                sub.index = i

            # Rafraîchir l'affichage
            self.tree.delete(*self.tree.get_children())
            self.populate_tree()

    def save_subtitles(self):
        """Sauvegarde des sous-titres"""
        try:
            self.subtitles.save("corrected_subtitles.srt")
            self.modified = False
            messagebox.showinfo("Succès", "Sous-titres sauvegardés avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def finish(self):
        """Fermeture de l'éditeur"""
        if self.modified:
            response = messagebox.askyesno(
                "Sauvegarder les modifications",
                "Voulez-vous sauvegarder les modifications avant de quitter?"
            )
            if response:
                self.save_subtitles()
        self.root.destroy()
        # Appel du callback pour continuer le traitement
        self.callback_after_save()

    def run(self) -> pysrt.SubRipFile:
        """Lancement de l'interface d'édition"""
        self.root.mainloop()
        result = self.subtitles  # Sauvegarde du résultat avant la destruction
        return result

class VideoProcessor:
    def __init__(self, video_path: str):
        """
        Gestionnaire de traitement vidéo
        """
        self.video_path = video_path

    def get_metadata(self) -> VideoMetadata:
        """Récupération des métadonnées de la vidéo"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "csv=p=0",
                self.video_path
            ]
            output = subprocess.check_output(cmd, universal_newlines=True)
            width, height, fps_str = output.strip().split(',')
            
            # Calcul du fps à partir de la fraction (ex: 30000/1001)
            num, den = map(int, fps_str.split('/'))
            fps = num / den
            
            return VideoMetadata(int(width), int(height), fps)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métadonnées: {e}")
            return VideoMetadata(1920, 1080, 30.0)
    


    def extract_audio(self, output_path: str) -> bool:
        """Extraction de l'audio de la vidéo"""
        try:
            command = [
                "ffmpeg",
                "-i", self.video_path,
                "-ar", "44100",
                "-ac", "2",
                "-vn",
                output_path
            ]
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'extraction audio: {e}")
            return False

    def overlay_subtitles(self, ass_file: str, output_path: str) -> bool:
        """Superposition des sous-titres sur la vidéo"""
        try:
            command = [
                "ffmpeg",
                "-i", self.video_path,
                "-vf", f"ass={ass_file}",
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ]
            subprocess.run(command, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de la superposition des sous-titres: {e}")
            return False

class SubtitleGenerator:
    def __init__(self, video_path: str):
        """
        Générateur de sous-titres avec interface d'édition
        """
        self.video_path = video_path
        self.video_processor = VideoProcessor(video_path)
        
        # Initialisation du modèle Whisper
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Utilisation du périphérique: {self.device}")
        self.model = whisper.load_model("large-v2", device=self.device)

    def transcribe_audio(self, audio_path: str) -> List[dict]:
        """Transcription de l'audio"""
        logger.info("Transcription de l'audio...")
        try:
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                fp16=True,
                language='fr'
            )
            return result["segments"]
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            raise

    def generate_srt(self, segments: List[dict]) -> pysrt.SubRipFile:
        """Génération du fichier SRT initial"""
        logger.info("Génération du fichier SRT...")
        subtitles = pysrt.SubRipFile()

        for i, segment in enumerate(segments):
            start_time = pysrt.SubRipTime(seconds=segment["start"] - 0.5)
            end_time = pysrt.SubRipTime(seconds=segment["end"])
            text = " ".join([word["word"] for word in segment["words"]])

            subtitles.append(
                pysrt.SubRipItem(
                    index=i + 1,
                    start=start_time,
                    end=end_time,
                    text=text
                )
            )

        return subtitles

    def generate_ass_style(self, metadata: VideoMetadata) -> str:
        """Génération du style ASS sans fond noir"""
        return f"""[Script Info]
Title: Sous-titres stylisés
ScriptType: v4.00+
PlayResX: {metadata.width}
PlayResY: {metadata.height}
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SubtitleFadeZoom,Arial,170,&HFFFFFF,&HFFFFFF,&H000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,0,2,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def format_ass_time(self, seconds: float) -> str:
        """Formatage du temps pour le format ASS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        centiseconds = int((secs - int(secs)) * 100)
        return f"{hours}:{minutes:02}:{int(secs):02}.{centiseconds:02}"
    
    def get_metadata(self) -> VideoMetadata:
        """Récupération des métadonnées de la vidéo"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "csv=p=0",
                self.video_path
            ]
            output = subprocess.check_output(cmd, universal_newlines=True)
            width, height, fps_str = output.strip().split(',')
            
            # Calcul du fps à partir de la fraction (ex: 30000/1001)
            num, den = map(int, fps_str.split('/'))
            fps = num / den
            
            return VideoMetadata(int(width), int(height), fps)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métadonnées: {e}")
            return VideoMetadata(1920, 1080, 30.0)

    def convert_to_ass(self, subtitles: pysrt.SubRipFile, metadata: VideoMetadata) -> str:
        """Conversion des sous-titres SRT en ASS avec fond rouge sur le mot prononcé,
        limité à 4 mots maximum par phrase, sans fond noir."""
        logger.info("Conversion en format ASS (effet sur le mot parlé)...")
        ass_file = "highlighted_subtitles.ass"

        metadata = self.get_metadata()
        logger.info(f"Dimensions vidéo : {metadata.width}x{metadata.height}, FPS : {metadata.fps}")

        # Générer les styles de base
        with open(ass_file, "w", encoding='utf-8') as f:
            f.write(self.generate_ass_style(metadata))

        # Position des sous-titres
        center_x = metadata.width // 2
        bottom_y = int(metadata.height * 0.9)

        with open(ass_file, "a", encoding='utf-8') as f:
            for sub in subtitles:
                # Diviser la phrase en groupes de 4 mots maximum
                words = sub.text.split()
                groups = [words[i:i+4] for i in range(0, len(words), 4)]
                
                total_duration = (sub.end.ordinal - sub.start.ordinal) / 1000.0
                words_per_group = len(words)
                word_duration = total_duration / words_per_group

                # Traiter chaque groupe de mots
                current_word_index = 0
                for group in groups:
                    for i, word in enumerate(group):
                        start_time = self.format_ass_time(sub.start.ordinal / 1000.0 + current_word_index * word_duration)
                        end_time = self.format_ass_time(sub.start.ordinal / 1000.0 + (current_word_index + 1) * word_duration)

                        # Style pour les mots normaux (vraiment sans fond)
                        base_style = (
                            f"\\an2"  # Alignement centré en bas
                            f"\\pos({center_x},{bottom_y})"
                            f"\\1c&HFFFFFF&"  # Texte blanc
                            f"\\3c&H000000&"  # Contour noir
                            f"\\4a&HFF&"      # Ombre totalement transparente
                            f"\\bord2"        # Contour fin
                            f"\\shad0"        # Pas d'ombre
                            f"\\fs170"        # Taille de police
                        )

                        # Style pour le mot en surbrillance (fond rouge)
                        highlight_style = (
                            f"\\an2"
                            f"\\pos({center_x},{bottom_y})"
                            f"\\1c&HFFFFFF&"  # Texte blanc
                            f"\\3c&H0000FF&"  # Contour rouge
                            f"\\4c&H0000FF&"  # Fond rouge
                            f"\\4a&H00&"      # Fond opaque
                            f"\\bord15"       # Large bordure pour créer le fond
                            f"\\shad0"        # Pas d'ombre
                            f"\\fs170"
                        )

                        # Construction du texte pour ce groupe
                        text_parts = []
                        for j, w in enumerate(group):
                            if j == i:
                                # Mot actuel avec fond rouge
                                text_parts.append(f"{{{highlight_style}}}{w}")
                            else:
                                # Autres mots (vraiment sans fond)
                                text_parts.append(f"{{{base_style}}}{w}")
                        
                        final_text = " ".join(text_parts)
                        f.write(f"Dialogue: 0,{start_time},{end_time},SubtitleFadeZoom,,0,0,0,,{final_text}\n")
                        current_word_index += 1

        logger.info("Conversion en ASS terminée.")
        return ass_file
        
    def run(self) -> bool:
        """Processus principal de génération des sous-titres"""
        try:
            # Récupération des métadonnées vidéo
            metadata = self.video_processor.get_metadata()
            logger.info(f"Métadonnées vidéo: {metadata}")

            # Extraction de l'audio
            audio_path = "temp_audio.wav"
            if not self.video_processor.extract_audio(audio_path):
                raise RuntimeError("Échec de l'extraction audio")

            # Transcription
            segments = self.transcribe_audio(audio_path)
            
            # Génération SRT
            subtitles = self.generate_srt(segments)
            
            # Interface d'édition
            editor = SubtitleEditor(subtitles)
            corrected_subtitles = editor.run()
            
            if corrected_subtitles is not None:  # Vérification que des sous-titres ont été retournés
                # Conversion en ASS avec effets
                ass_file = self.convert_to_ass(corrected_subtitles, metadata)
                
                # Superposition des sous-titres
                output_path = "video_with_subtitles.mp4"
                if not self.video_processor.overlay_subtitles(ass_file, output_path):
                    raise RuntimeError("Échec de la superposition des sous-titres")

                # Nettoyage
                if os.path.exists(audio_path):
                    os.remove(audio_path)

                logger.info("Traitement terminé avec succès!")
                return True
            else:
                logger.warning("L'édition des sous-titres a été annulée")
                return False

        except Exception as e:
            logger.error(f"Erreur lors du traitement: {str(e)}")
            return False

def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    root.withdraw()

    try:
        video_path = filedialog.askopenfilename(
            title="Sélectionner une vidéo",
            filetypes=[
                ("Fichiers vidéo", "*.mp4 *.avi *.mkv *.mov"),
                ("Tous les fichiers", "*.*")
            ]
        )

        if not video_path:
            logger.info("Aucune vidéo sélectionnée.")
            root.destroy()
            return

        # Création et exécution du générateur de sous-titres
        generator = SubtitleGenerator(video_path)
        
        try:
            # Récupération des métadonnées vidéo
            metadata = generator.video_processor.get_metadata()
            logger.info(f"Métadonnées vidéo: {metadata}")

            # Extraction de l'audio
            audio_path = "temp_audio.wav"
            if not generator.video_processor.extract_audio(audio_path):
                raise RuntimeError("Échec de l'extraction audio")

            # Transcription
            segments = generator.transcribe_audio(audio_path)
            
            # Génération SRT
            subtitles = generator.generate_srt(segments)
            
            def continue_processing():
                try:
                    # Conversion en ASS avec effets
                    ass_file = generator.convert_to_ass(subtitles, metadata)
                    
                    # Superposition des sous-titres
                    output_path = "video_with_subtitles.mp4"
                    if not generator.video_processor.overlay_subtitles(ass_file, output_path):
                        raise RuntimeError("Échec de la superposition des sous-titres")

                    # Nettoyage
                    if os.path.exists(audio_path):
                        os.remove(audio_path)

                    logger.info("Traitement terminé avec succès!")
                    messagebox.showinfo(
                        "Succès",
                        "Traitement terminé avec succès!\n"
                        "Les fichiers suivants ont été générés:\n"
                        "- corrected_subtitles.srt\n"
                        "- styled_subtitles.ass\n"
                        "- video_with_subtitles.mp4"
                    )
                    root.destroy()
                except Exception as e:
                    logger.error(f"Erreur lors du traitement final: {str(e)}")
                    messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
                    root.destroy()

            # Interface d'édition
            editor = SubtitleEditor(subtitles, continue_processing)
            editor.root.mainloop()
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement: {str(e)}")
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
            root.destroy()

    except Exception as e:
        logger.error(f"Erreur principale: {str(e)}")
        messagebox.showerror("Erreur critique", str(e))
        root.destroy()

if __name__ == "__main__":
    main()