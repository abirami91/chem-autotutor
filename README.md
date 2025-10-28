🧪 Chem-Autotutor

Generate mini molecule tutorials — complete with 3D viewer, voiceover script, captions, and YouTube description.

✨ Overview

Chem-Autotutor automatically builds a tutorial for any molecule given its IUPAC name, SMILES, or formula.
It uses:

* OPSIN
 → converts chemical names → SMILES

* RDKit
 → computes 2D/3D structure & properties

* Jinja2
 → renders HTML pages with interactive 3D viewer

* Docker → reproducible, no messy dependencies

Each run generates:

out/
 └── <molecule>/
      ├── index.html             ← Interactive 3D page (view in browser)
      ├── model.sdf              ← 3D coordinates
      ├── model.png              ← 2D Kekulé image
      ├── voiceover.txt          ← narration script
      ├── captions.srt           ← subtitle file
      └── YOUTUBE_DESCRIPTION.md ← ready-to-paste description

🧰 1. Setup
## Option A — Docker (recommended)
    
    git clone https://github.com/abirami91/chem-autotutor.git
    cd chem-autotutor
    docker build -t chem-autotutor:latest .
    

Option B — Local (manual)

Requires:

* Python ≥3.9

* Java ≥17

* RDKit, Jinja2

* OPSIN JAR (auto-downloaded)

Install:

* pip install rdkit-pypi jinja2

⚙️ 2. Usage

The easiest way is via the included Makefile:

Command	Input	Description
* make name NAME="4-bromo-3-methylhept-1-en-6-yne"	IUPAC name	Generates tutorial from OPSIN name
* make smiles SMILES="C/C=C(CBr)CC#C"	SMILES	Generates tutorial directly
* make formula FORMULA="C8H12Br"	Molecular formula	Text-only facts
* make build	—	Rebuild Docker image
* make clean	—	Clean all outputs

Output will appear under out/<slug>/index.html.

Open that file in your browser to explore the molecule in 3D.

🧠 3. Example
make name NAME="4-bromo-3-methylhept-1-en-6-yne"


Output:

✅ Done.
Open out/4-bromo-3-methylhept-1-en-6-yne/index.html

🎬 4. Exporting for YouTube

Each generated folder contains:

* index.html — your 3D viewer (screen record this for video)

* voiceover.txt — narration script

* captions.srt — subtitle timings

* YOUTUBE_DESCRIPTION.md — ready to paste description

🧩 Suggested workflow

* Open index.html → Screen record it (use OBS/CapCut/QuickTime).

* Use voiceover.txt as narration (you can record yourself or use TTS).

* Add captions.srt as subtitles in YouTube upload settings.

* Paste the text from YOUTUBE_DESCRIPTION.md as your video description.

* Thumbnail tip → take a screenshot of the molecule’s 3D viewer.

Optional tools:

sudo apt install obs-studio ffmpeg

💡 5. Example YouTube title & description

Title:

4-Bromo-3-Methylhept-1-En-6-Yne | 3D Molecule Explained | Chem-Autotutor

Description (already generated for you):

This video shows the 3D structure and quick facts of 4-Bromo-3-Methylhept-1-En-6-Yne.
Generated using Chem-Autotutor (RDKit + OPSIN).

Learn chemistry visually — one molecule at a time!
https://github.com/abirami91/chem-autotutor
#Chemistry #3DVisualization #Molecules

🧩 6. Future enhancements

✅ Voiceover automation (Edge-TTS integration)

✅ SMILES validation (auto-correction for halogen valence)

🔜 Batch processing multiple molecules from a CSV

🔜 Web frontend with molecule input + render preview

👩‍🔬 Author

Abirami Sridharan
🧬 Passionate about computational chemistry, automation, and creative science communication.
📺 YouTube: Chem-Autotutor (coming soon!)
🌐 GitHub: @abirami91

⚖️ License

MIT License — free for educational and research use.
