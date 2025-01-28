# Générateur de Sous-titres Vidéo

Une application Python qui permet de générer, éditer et incruster automatiquement des sous-titres sur des vidéos, avec un effet de surlignage des mots au moment où ils sont prononcés.

## Fonctionnalités

- Transcription automatique de l'audio en texte via Whisper
- Interface graphique pour l'édition des sous-titres
- Génération de sous-titres animés avec effet de surlignage
- Support des formats vidéo courants (MP4, AVI, MKV, MOV)
- Export en formats SRT et ASS
- Incrustation des sous-titres dans la vidéo

## Prérequis

- Python 3.8+
- FFmpeg installé et accessible dans le PATH
- CUDA-compatible GPU (recommandé)

### Dépendances Python

```bash
pip install torch whisper pysrt tkinter
```

## Installation

1. Clonez le dépôt :
```bash
git clone [url-du-repo]
cd video-subtitles-generator
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Vérifiez que FFmpeg est installé :
```bash
ffmpeg -version
```

## Utilisation

1. Lancez l'application :
```bash
python main.py
```

2. L'interface vous guidera à travers les étapes suivantes :
   - Sélection du fichier vidéo
   - Transcription automatique
   - Édition des sous-titres
   - Génération de la vidéo finale

### Interface d'édition des sous-titres

L'éditeur de sous-titres permet de :
- Visualiser tous les sous-titres dans un tableau
- Ajouter, modifier ou supprimer des sous-titres
- Ajuster les temps de début et de fin
- Corriger le texte transcrit

## Structure du projet

```
├── main.py                  # Point d'entrée de l'application
├── classes/
│   ├── SubtitleEditor      # Interface d'édition des sous-titres
│   ├── VideoProcessor      # Gestion des opérations vidéo
│   └── SubtitleGenerator   # Génération et traitement des sous-titres
```

## Fichiers générés

L'application génère les fichiers suivants :
- `corrected_subtitles.srt` : Sous-titres au format SRT
- `highlighted_subtitles.ass` : Sous-titres stylisés au format ASS
- `video_with_subtitles.mp4` : Vidéo finale avec sous-titres incrustés

## Détails techniques

### Traitement des sous-titres

- Le modèle Whisper "large-v2" est utilisé pour la transcription
- Les sous-titres sont synchronisés au niveau des mots
- L'effet de surlignage utilise le format ASS pour l'animation
- La taille des sous-titres est adaptée automatiquement à la résolution de la vidéo

### Performance

- Utilisation automatique du GPU si disponible
- Optimisation FFmpeg pour la qualité vidéo (preset slow, CRF 18)
- Audio converti en 44.1kHz stéréo pour une compatibilité optimale

## Personnalisation

Les paramètres suivants peuvent être ajustés dans le code :
- Taille et style des sous-titres (`generate_ass_style`)
- Couleurs et effets (`convert_to_ass`)
- Paramètres de compression vidéo (`overlay_subtitles`)

## Dépannage

### Problèmes courants

1. **FFmpeg non trouvé** :
   - Vérifiez que FFmpeg est installé
   - Ajoutez FFmpeg au PATH système

2. **Erreur CUDA** :
   - Vérifiez l'installation des pilotes NVIDIA
   - Le CPU sera utilisé automatiquement en fallback

3. **Erreur de mémoire** :
   - Libérez de la mémoire RAM/VRAM
   - Utilisez une vidéo de résolution inférieure

## Contributions

Les contributions sont les bienvenues ! Veuillez :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

