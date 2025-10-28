#!/usr/bin/env python3
"""
chem-autotutor — Generate a mini tutorial for any molecule.

Inputs (mutually exclusive):
  --name "4-bromo-3-methylhept-1-en-6-yne"   # IUPAC -> uses OPSIN jar to get SMILES
  --smiles "CCC([Br]CC#C)=C"                 # SMILES string
  --inchi "InChI=1S/..."                     # InChI string
  --formula "C8H12Br"                        # Formula-only mode (no unique 3D)

Outputs (in out/<TITLE>/):
  - index.html            # Interactive 3D viewer page (3Dmol.js)
  - structure.png         # 2D structure image (kekulized)
  - model.sdf             # 3D structure (SDF text)
  - voiceover.txt         # Narration draft for recording/TTS
  - captions.srt          # SubRip captions (simple timing)
  - YOUTUBE_DESCRIPTION.md# Paste this into YouTube description

Dependencies:
  - Java 17+ (for OPSIN)
  - OPSIN jar (downloaded into repo as opsin.jar)
  - Python: rdkit-pypi, jinja2
"""

import os, argparse, subprocess
from pathlib import Path
from jinja2 import Template
from rdkit import Chem
from rdkit.Chem import AllChem, Draw, rdMolDescriptors

# --- Paths relative to this script ---
HERE = Path(__file__).parent
TPL_HTML = HERE / "templates" / "page.html.j2"       # HTML template for the tutorial page
TPL_YT   = HERE / "templates" / "youtube_desc.md.j2" # Template for YouTube description
OPSIN    = HERE / "opsin.jar"                        # OPSIN jar for name->SMILES

def ensure_out(dirpath: Path) -> Path:
    """
    Create output directory if missing and return it.
    Example: out/4-bromo-3-methylhept-1-en-6-yne/
    """
    dirpath.mkdir(parents=True, exist_ok=True)
    return dirpath

def name_to_smiles(name: str) -> str:
    """
    OPSIN 2.8.0 CLI expects files:
      java -jar opsin.jar -osmi input.txt output.txt
    This writes the name to a temp input file and reads SMILES from a temp output file.
    """
    import tempfile, os, subprocess, pathlib

    in_fd, in_path = tempfile.mkstemp(prefix="opsin_in_", text=True)
    out_fd, out_path = tempfile.mkstemp(prefix="opsin_out_", text=True)
    os.close(in_fd); os.close(out_fd)

    try:
        pathlib.Path(in_path).write_text(name.strip() + "\n", encoding="utf-8")
        cmd = ["java", "-jar", str(OPSIN), "-osmi", in_path, out_path]
        # (Optional) add '-v' here to get verbose parsing diagnostics:
        # cmd = ["java","-jar",str(OPSIN),"-v","-osmi",in_path,out_path]
        subprocess.check_call(cmd)

        out = pathlib.Path(out_path).read_text(encoding="utf-8").strip()
        # OPSIN writes one SMILES per line (may be tab-delimited if name flag enabled)
        smi = out.splitlines()[0].split()[0]
        if not smi:
            raise RuntimeError("OPSIN returned empty SMILES")
        return smi
    finally:
        for p in (in_path, out_path):
            try: os.unlink(p)
            except OSError: pass




def mol_from_any(name=None, smiles=None, inchi=None):
    """
    Create an RDKit Mol object (with explicit Hs) from any accepted input.
    Returns: (Mol_with_Hs, smiles_string)
    """
    if name:
        smiles = name_to_smiles(name)            # name -> SMILES via OPSIN
    if inchi:
        mol = Chem.MolFromInchi(inchi)           # InChI -> Mol
    else:
        mol = Chem.MolFromSmiles(smiles)         # SMILES -> Mol
    if mol is None:
        raise ValueError("Could not parse structure from input.")
    mol = Chem.AddHs(mol)                        # add explicit hydrogens for 3D embedding
    return mol, (smiles if smiles else Chem.MolToSmiles(mol))

def formula_du(nC, nH, nN=0, nX=0):
    """
    Degree of Unsaturation (Index of Hydrogen Deficiency) for CHN + halogens.

    DU = 1 + C - (H_equiv)/2
    where H_equiv = H + X - N  (X = halogens: F, Cl, Br, I)

    DU counts: rings + double bonds + 2*triple bonds.
    """
    h_equiv = nH + nX - nN
    return 1 + nC - h_equiv / 2

def compute_facts(mol):
    """
    Compute formula, exact mass, and DU from an RDKit Mol.
    - Uses RDKit to compute the chemical formula and exact mass.
    - Parses element counts for DU computation.
    Returns: (formula_str, exact_mass_float, du_float)
    """
    formula = rdMolDescriptors.CalcMolFormula(mol)
    mw = round(rdMolDescriptors.CalcExactMolWt(mol), 4)

    # Parse element counts from formula for DU calculation.
    # Note: CalcMolFormula returns e.g. 'C8H12Br' (compact form).
    import re
    counts = dict(re.findall(r'([A-Z][a-z]?)(\d*)', formula))

    def get(sym):
        """
        Extract integer count for an element symbol.
        Empty count means '1'.
        """
        v = counts.get(sym)
        if v is None:
            return 0
        return int(v) if v != "" else 1

    nC  = get('C')
    nH  = get('H')
    nN  = get('N')
    nF  = get('F')
    nCl = get('Cl')
    nBr = get('Br')
    nI  = get('I')

    du = formula_du(nC, nH, nN, nF + nCl + nBr + nI)
    return formula, mw, du

def make_artifacts(mol, outdir: Path):
    """
    Generate 3D SDF (with ETKDG embedding + UFF minimization) and
    a 2D PNG (kekulized).
    Returns: SDF block (string)
    """
    # --- 3D conformer generation ---
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())       # geometry guess
    AllChem.UFFOptimizeMolecule(mol, maxIters=200)    # quick energy minimization
    sdf = Chem.MolToMolBlock(mol)                     # SDF text block
    (outdir / "model.sdf").write_text(sdf)

    # --- 2D depiction ---
    mol2d = Chem.RemoveHs(Chem.Mol(mol))              # cleaner 2D drawing
    AllChem.Compute2DCoords(mol2d)
    Draw.MolToFile(
        mol2d, str(outdir / "structure.png"),
        size=(800, 520),
        kekulize=True
    )
    return sdf

def render_html(title, smiles, formula, mw, sdf, bullets, outdir: Path):
    """
    Render the HTML tutorial page from the Jinja2 template.
    - Embeds SDF into the page for 3Dmol.js
    - Shows 2D image, formula, MW, SMILES, and teaching bullets.
    """
    html = Template(TPL_HTML.read_text()).render(
        title=title, smiles=smiles, formula=formula, mw=mw,
        sdf=sdf, bullets=bullets
    )
    (outdir / "index.html").write_text(html)

def make_bullets_from_name(name: str):
    """
    Very light heuristic to generate teaching bullets from the IUPAC name.
    Keeps it generic (works for many names).
    """
    if not name:
        return []
    b = []
    if "meth" in name:  b.append("Parent chain includes: meth- (1 carbon).")
    if "eth"  in name:  b.append("Parent chain includes: eth- (2 carbons).")
    if "prop" in name:  b.append("Parent chain includes: prop- (3 carbons).")
    if "but"  in name:  b.append("Parent chain includes: but- (4 carbons).")
    if "pent" in name:  b.append("Parent chain includes: pent- (5 carbons).")
    if "hex"  in name:  b.append("Parent chain includes: hex- (6 carbons).")
    if "hept" in name:  b.append("Parent chain includes: hept- (7 carbons).")
    if "oct"  in name:  b.append("Parent chain includes: oct- (8 carbons).")
    if "non"  in name:  b.append("Parent chain includes: non- (9 carbons).")
    if "dec"  in name:  b.append("Parent chain includes: dec- (10 carbons).")
    if "en" in name:    b.append("Contains a C=C double bond (-en-).")
    if "yn" in name:    b.append("Contains a C≡C triple bond (-yn-).")
    if "methyl" in name: b.append("Has a methyl (-CH₃) substituent.")
    if "bromo" in name:  b.append("Has a bromine substituent.")
    return b

def make_script(title, formula, mw, smiles, du):
    """
    Produce a simple narration (voiceover.txt) and timed captions (captions.srt).
    - Bullets are spaced every ~3 seconds in the SRT for quick demos.
    """
    bullets = [
        f"Title: {title}",
        f"Formula: {formula} | Exact mass {mw} u | SMILES: {smiles}",
        f"Unsaturation (rings + double + 2*triple): DU = {du:.1f}",
        "Naming checklist: longest chain, lowest locants for multiple bonds, then substituents alphabetically."
    ]
    voiceover = "\n".join(bullets)

    # Build a minimal SRT timeline
    srt_lines = []
    t = 0
    for i, line in enumerate(bullets, 1):
        srt_lines.append(
            f"{i}\n00:00:{t:02d},000 --> 00:00:{t+3:02d},000\n{line}\n"
        )
        t += 3
    return voiceover, "\n".join(srt_lines)


def render_html(title, smiles, formula, mw, sdf, bullets, outdir: Path,
                du=None, tutorial_id=None, subtitle=""):
    """
    Render the HTML tutorial page with optional tutorial metadata.
    """
    html = Template((TPL_HTML).read_text()).render(
        title=title,
        subtitle=subtitle,
        tutorial_id=tutorial_id,
        smiles=smiles,
        formula=formula,
        mw=mw,
        sdf=sdf,
        bullets=bullets,
        du=du
    )
    (outdir / "index.html").write_text(html)

def main():
    ap = argparse.ArgumentParser(description="Auto-build chemistry tutorial")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--name")
    g.add_argument("--smiles")
    g.add_argument("--inchi")
    g.add_argument("--formula")
    ap.add_argument("--tutorial", help="Optional subtitle/title for the tutorial (e.g., 'Tutorial 01 — Intro to Multiple Bonds')")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    title = args.name or args.smiles or args.inchi or args.formula
    outdir = ensure_out(Path(args.out) / slugify(title))

    if args.formula:
        # formula-only mode
        sdf = ""
        bullets = [
            "A single molecular formula can represent many isomers.",
            "Use degree of unsaturation (DU) to infer rings/double/triple bonds.",
            "Provide IUPAC name or SMILES to render a unique 3D structure."
        ]
        render_html(
            title=title,
            smiles=smiles,
            formula=formula,
            mw=mw,
            sdf=sdf,
            bullets=bullets,
            du=du,
            outdir=outdir,
            tutorial_id="Tutorial 01",
            subtitle=args.tutorial or "Understanding Alkene and Alkyne Substitution Patterns"
        )

        (outdir/"README.txt").write_text("Formula-only mode. Provide --name/--smiles to get 3D and facts.")
        print(f"ℹ️ Generated formula-only explainer at {outdir/'index.html'}")
        return

    # structure mode
    mol, smiles = mol_from_any(args.name, args.smiles, args.inchi)
    formula, mw, du = compute_facts(mol)
    sdf = make_artifacts(mol, outdir)
    bullets = make_bullets_from_name(args.name) if args.name else []
    # include DBE/DU note at the end
    bullets = (bullets or []) + [f"Double-bond equivalents (DU): {du:.1f}"]

    render_html(title, smiles, formula, mw, sdf, bullets, outdir, subtitle=args.tutorial or "")

    voiceover, srt = make_script(title, formula, mw, smiles, du)
    (outdir/"voiceover.txt").write_text(voiceover)
    (outdir/"captions.srt").write_text(srt)

    yt = Template((TPL_YT).read_text()).render(
        title=title, smiles=smiles, formula=formula, mw=mw
    )
    (outdir/"YOUTUBE_DESCRIPTION.md").write_text(yt)

    print("✅ Done.")
    print(f"Open {outdir/'index.html'} (interactive 3D). See voiceover.txt and captions.srt.")
    print(f"YouTube description ready at {outdir/'YOUTUBE_DESCRIPTION.md'}.")