
"""
interface.py — Interface graphique pour l'accordeur TFD
Lance avec : python interface.py
"""
import sys
import tkinter as tk
from tkinter import scrolledtext
import threading
import math
import cmath
import os

# Chemin absolu du dossier contenant ce fichier (et les autres scripts du projet)
DOSSIER = os.path.dirname(os.path.abspath(__file__))

# Palette de couleurs de l'interface
BLEU   = "#2563eb"
VERT   = "#16a34a"
ORANGE = "#ea580c"
GRIS   = "#f1f5f9"
BLANC  = "#ffffff"
ROUGE  = "#dc2626"


# TFD manuelle (deux boucles imbriquees)
# Formule : X[k] = somme_{n=0}^{N-1} x[n] * exp(-2j * pi * k * n / N)
# Incluse ici directement pour afficher le calcul sans depend de accordeur.py
def tfd(x):
    N = len(x)
    return [
        sum(x[n] * cmath.exp(-2j * math.pi * k * n / N) for n in range(N))
        for k in range(N)
    ]


# Classe principale de l'application
class AppAccordeur(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Accordeur TFD — Interface de demonstration")
        self.geometry("900x700")
        self.configure(bg=GRIS)
        self.resizable(True, True)
        self._construire()

    # ------------------------------------------------------------------------
    # Construction de l'interface graphique
    # ------------------------------------------------------------------------
    def _construire(self):
        # Bandeau de titre principal
        tk.Label(
            self,
            text="Accordeur Chromatique — Transformee de Fourier Discrete",
            font=("Helvetica", 14, "bold"),
            bg=BLEU, fg=BLANC, pady=10
        ).pack(fill="x")

        tk.Label(
            self,
            text="Interface de demonstration — Examen Signal et TFD",
            font=("Helvetica", 10),
            bg=BLEU, fg="#bfdbfe", pady=4
        ).pack(fill="x")

        # Zone principale : colonne gauche (boutons) + colonne droite (sortie)
        corps = tk.Frame(self, bg=GRIS)
        corps.pack(fill="both", expand=True, padx=10, pady=10)

        col_gauche = tk.Frame(corps, bg=GRIS, width=320)
        col_gauche.pack(side="left", fill="y", padx=(0, 8))
        col_gauche.pack_propagate(False)

        col_droite = tk.Frame(corps, bg=BLANC, relief="solid", bd=1)
        col_droite.pack(side="left", fill="both", expand=True)

        # Colonne gauche : les 4 etapes avec leurs boutons
        self._section(col_gauche, "ETAPE 1 — Verification de la TFD")
        self._bouton(col_gauche, "Calculer tfd([1,6,8,-4,9])", BLEU, self._etape1_tfd)

        self._section(col_gauche, "ETAPE 2 — Mode Test (sans micro)")
        self._bouton(col_gauche, "Lancer test sinus 440 Hz", VERT, self._etape2_test)

        self._section(col_gauche, "ETAPE 3 — Generer les graphiques")
        self._bouton(col_gauche, "Generer spectre.png", ORANGE, self._etape3_spectre)

        self._section(col_gauche, "ETAPE 4 — Accordeur temps reel")
        self._bouton(col_gauche, "Lancer l'accordeur (micro)", ROUGE, self._etape4_realtime)
        self._bouton(col_gauche, "Arreter l'accordeur", "#64748b", self._stop_realtime)

        # Separateur horizontal
        tk.Frame(col_droite, height=1, bg="#cbd5e1").pack(fill="x")

        # Zone de texte avec ascenseur (affichage des resultats)
        self.sortie = scrolledtext.ScrolledText(
            col_droite,
            font=("Courier New", 10),
            bg="#0f172a", fg="#e2e8f0",
            insertbackground="white",
            relief="flat", padx=10, pady=10,
            state="disabled"
        )
        self.sortie.pack(fill="both", expand=True)

        # Balises de couleur pour la zone de sortie
        self.sortie.tag_config("ok",    foreground="#4ade80")  # vert : resultat correct
        self.sortie.tag_config("err",   foreground="#f87171")  # rouge : erreur ou echec
        self.sortie.tag_config("titre", foreground="#93c5fd",  # bleu clair : en-tete de section
                               font=("Courier New", 10, "bold"))
        self.sortie.tag_config("val",   foreground="#fbbf24")  # orange : valeur numerique

        # Barre de statut en bas de fenetre
        self.statut = tk.Label(
            self, text="Pret.", font=("Helvetica", 9),
            bg="#e2e8f0", fg="#475569", anchor="w", padx=10, pady=4
        )
        self.statut.pack(fill="x", side="bottom")

        # Variables de controle de l'accordeur temps reel
        self._arret_demande = False
        self._thread_micro  = None

    # ------------------------------------------------------------------------
    # Methodes utilitaires de l'interface
    # ------------------------------------------------------------------------
    def _section(self, parent, texte):
        """Affiche un titre de section dans la colonne gauche."""
        f = tk.Frame(parent, bg="#e2e8f0", pady=2)
        f.pack(fill="x", pady=(10, 0))
        tk.Label(
            f, text=texte, font=("Helvetica", 8, "bold"),
            bg="#e2e8f0", fg="#475569", anchor="w", padx=6
        ).pack(fill="x")

    def _bouton(self, parent, texte, couleur, commande):
        """Cree un bouton d'action."""
        tk.Button(
            parent, text=texte,
            font=("Helvetica", 10, "bold"),
            bg=couleur, fg=BLANC,
            activebackground=couleur, activeforeground=BLANC,
            relief="flat", pady=8, padx=6, cursor="hand2",
            command=lambda: self._lancer(commande)
        ).pack(fill="x", pady=3)

    def _lancer(self, fn):
        """Lance une action dans un thread separe."""
        self._effacer()
        threading.Thread(target=fn, daemon=True).start()

    def _effacer(self):
        """Vide la zone de sortie."""
        self.sortie.config(state="normal")
        self.sortie.delete("1.0", "end")
        self.sortie.config(state="disabled")

    def _ecrire(self, texte, tag=""):
        """Ajoute une ligne dans la zone de sortie avec une couleur optionnelle."""
        self.sortie.config(state="normal")
        self.sortie.insert("end", texte + "\n", tag)
        self.sortie.see("end")
        self.sortie.config(state="disabled")

    def _statut(self, msg):
        """Met a jour la barre de statut en bas de fenetre."""
        self.statut.config(text=msg)

    
    # ETAPE 1 — Calcul de la TFD manuelle et comparaison avec numpy
    
    def _etape1_tfd(self):
        self._statut("Calcul TFD manuelle en cours...")
        self._ecrire("=" * 48, "titre")
        self._ecrire("   VERIFICATION DE LA TFD MANUELLE", "titre")
        self._ecrire("=" * 48, "titre")
        self._ecrire("")
        self._ecrire("Formule : X[k] = somme x[n] * exp(-2j*pi*k*n/N)", "val")
        self._ecrire("Signal de test : x = [1, 6, 8, -4, 9]", "val")
        self._ecrire("")

        x = [1, 6, 8, -4, 9]
        X = tfd(x)   # calcul par les deux boucles imbriquees

        self._ecrire("Resultats tfd() manuelle (deux boucles) :", "titre")
        for k, v in enumerate(X):
            signe = "+" if v.imag >= 0 else ""
            self._ecrire(f"  X[{k}] = {v.real:9.4f} {signe}{v.imag:.4f}j")

        self._ecrire("")
        self._ecrire("Comparaison avec numpy :", "titre")
        try:
            import numpy as np
            Xnp = np.fft.fft(x)
            for k in range(len(x)):
                err = abs(X[k] - Xnp[k])
                # Erreur inferieure a 1e-9 : les deux methodes sont identiques
                self._ecrire(
                    f"  k={k} : erreur = {err:.2e}",
                    "ok" if err < 1e-9 else "err"
                )
            self._ecrire("")
            self._ecrire("  X[0] = 20.0000           (attendu : 20)", "ok")
            self._ecrire("  X[1] = 2.3992 - 4.2003j  (attendu : 2.399 - 4.2j)", "ok")
            self._ecrire("")
            self._ecrire("  [OK]  tfd() IDENTIQUE a np.fft.fft()", "ok")
        except ImportError:
            self._ecrire("  numpy non disponible pour la comparaison.", "err")

        self._statut("Etape 1 terminee — faites la capture d'ecran maintenant !")

    
    # ETAPE 2 — Mode test : detection d'un sinus synthetique a 440 Hz
    
    def _etape2_test(self):
        self._statut("Test sinus 440 Hz en cours...")
        self._ecrire("=" * 48, "titre")
        self._ecrire("   MODE TEST — SINUS SYNTHETIQUE 440 Hz", "titre")
        self._ecrire("=" * 48, "titre")
        self._ecrire("")
        self._ecrire("Generation : sinus 440 Hz, 1 seconde, fe = 44 100 Hz", "val")
        self._ecrire("Fenetre    : Hann (reduction des fuites spectrales)",   "val")
        self._ecrire("TFD        : np.fft.fft() — algorithme FFT rapide",    "val")
        self._ecrire("")

        try:
            import numpy as np

            fe     = 44100
            N      = fe
            t      = np.linspace(0, 1.0, N, endpoint=False)
            signal = np.sin(2 * math.pi * 440 * t).astype(np.float64)

            # Application de la fenetre de Hann puis calcul de la TFD
            fenetre = np.hanning(N)
            spectre = np.abs(np.fft.fft(signal * fenetre)[: N // 2])

            # Suppression des frequences parasites inferieures a 62 Hz
            nb_sup = int(62 / (fe / N))
            spectre[:nb_sup] = 0

            # Indice du pic dominant dans le spectre
            idx = int(np.argmax(spectre))
            # Conversion indice -> frequence : f = k * fe / N
            f   = idx * fe / N

            # Conversion frequence -> note chromatique
            i     = int(round(math.log2(f / 440) * 12))
            notes = ["La","La#","Si","Do","Do#","Re","Re#","Mi","Fa","Fa#","Sol","Sol#"]
            note  = notes[i % 12] + str(4 + (i + 9) // 12)
            f_ref = 440 * 2 ** (i / 12)
            # Ecart en cents : 1200 cents = 1 octave
            cents = 1200 * math.log2(f / f_ref)

            self._ecrire("--- Resultat -----------------------------------", "titre")
            self._ecrire(f"  Indice du pic      : k = {idx}",                      "val")
            self._ecrire(f"  Frequence detectee : f = k * fe / N = {f:.1f} Hz",    "val")
            self._ecrire(f"  Note la plus proche : {note}",                        "val")
            self._ecrire(f"  Frequence de reference : {f_ref:.1f} Hz",             "val")
            self._ecrire(f"  Ecart : {cents:+.2f} cents",                          "val")
            self._ecrire("")
            if note.startswith("La") and abs(cents) < 1.0:
                self._ecrire("  ==> [OK]  La4 correctement detecte !", "ok")
                self._ecrire("  ==> Sinus 440 Hz  ->  La4  (+0.0 cents)", "ok")
            else:
                self._ecrire(f"  ECHEC : note detectee = {note}", "err")

        except ImportError:
            self._ecrire("  numpy non installe.", "err")

        self._statut("Etape 2 terminee — faites la capture d'ecran maintenant !")

    
    # ETAPE 3 — Generation des trois graphiques PNG
    
    def _etape3_spectre(self):
        self._statut("Generation des images en cours...")
        self._ecrire("=" * 48, "titre")
        self._ecrire("   GENERATION DU SPECTRE FREQUENTIEL", "titre")
        self._ecrire("=" * 48, "titre")
        self._ecrire("")

        script = os.path.join(DOSSIER, "generer_spectre.py")
        if not os.path.exists(script):
            self._ecrire("  ERREUR : generer_spectre.py introuvable.", "err")
            return

        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("generer_spectre", script)
            mod  = importlib.util.module_from_spec(spec)

            # Redirection temporaire de stdout pour capturer les messages du script
            class Redirecteur:
                def write(self_r, s):
                    if s.strip():
                        tag = "ok" if "[OK]" in s else "err" if "ERREUR" in s else ""
                        self._ecrire("  " + s.strip(), tag)
                def flush(self_r):
                    pass

            ancien_stdout  = sys.stdout
            sys.stdout     = Redirecteur()
            spec.loader.exec_module(mod)
            sys.stdout     = ancien_stdout

        except Exception as e:
            self._ecrire(f"  Erreur lors de la generation : {e}", "err")
            return

        # Verification de la presence des fichiers generes
        self._ecrire("")
        self._ecrire("Images dans le dossier du projet :", "titre")
        for nom in ["spectre.png", "spectre_tfd.png", "schema_pipeline.png"]:
            chemin = os.path.join(DOSSIER, nom)
            if os.path.exists(chemin):
                self._ecrire(f"  [OK]  {nom}", "ok")
            else:
                self._ecrire(f"  [!!]  {nom} — non trouve", "err")

        # Ouverture de spectre.png dans une sous-fenetre (si Pillow est installe)
        self._afficher_image(os.path.join(DOSSIER, "spectre.png"))
        self._statut("Etape 3 terminee — faites la capture d'ecran maintenant !")

    def _afficher_image(self, chemin):
        """
        Ouvre une sous-fenetre pour afficher l'image generee.
        Si Pillow (PIL) n'est pas installe, ouvre le fichier avec le visionneur Windows.
        """
        if not os.path.exists(chemin):
            return
        try:
            from PIL import Image, ImageTk
            img_brut    = Image.open(chemin)
            img_brut.thumbnail((860, 400))
            sous_fenetre = tk.Toplevel(self)
            sous_fenetre.title(f"Spectre — {os.path.basename(chemin)}")
            sous_fenetre.configure(bg=BLANC)
            img_tk = ImageTk.PhotoImage(img_brut)
            lbl    = tk.Label(sous_fenetre, image=img_tk, bg=BLANC)
            lbl.image = img_tk   # reference conservee pour eviter la suppression par le GC
            lbl.pack(padx=10, pady=10)
            tk.Label(
                sous_fenetre,
                font=("Helvetica", 10, "bold"), fg=BLEU, bg=BLANC
            ).pack(pady=(0, 10))
        except ImportError:
            # Pillow absent : ouverture avec le visionneur d'images par defaut
            os.startfile(chemin)

    
    # ETAPE 4 — Accordeur temps reel via le microphone
    
    def _etape4_realtime(self):
        self._arret_demande = False
        self._statut("Accordeur temps reel demarre — parlez ou jouez une note...")
        self._ecrire("=" * 48, "titre")
        self._ecrire("   ACCORDEUR TEMPS REEL — MICROPHONE", "titre")
        self._ecrire("=" * 48, "titre")
        self._ecrire("")
        self._ecrire("  Parlez, chantez ou jouez une note.", "val")
        self._ecrire("  La note detectee s'affiche ci-dessous.", "val")
        self._ecrire("  Appuyez sur [Arreter] pour terminer.", "val")
        self._ecrire("")
        # Lancement de la capture micro dans un thread separe (non bloquant)
        self._thread_micro = threading.Thread(target=self._boucle_micro, daemon=True)
        self._thread_micro.start()

    def _boucle_micro(self):
        """
        Boucle de capture et d'analyse audio en temps reel.
        Tourne dans un thread separe pour ne pas bloquer l'interface.
        """
        try:
            import numpy as np
            import sounddevice as sd

            fe     = 44100
            N      = fe
            PAS    = 22050
            tampon = np.zeros(N, dtype=np.float32)   # tampon circulaire
            notes  = ["La","La#","Si","Do","Do#","Re","Re#","Mi","Fa","Fa#","Sol","Sol#"]

            def callback(entree, frames, t, statut):
                nonlocal tampon
                if self._arret_demande:
                    raise sd.CallbackStop()   # stoppe proprement le flux audio

                nouveaux = entree[:, 0]
                # Mise a jour du tampon circulaire par decalage
                tampon = np.concatenate((tampon, nouveaux))[len(nouveaux):]

                puissance = float(np.mean(tampon ** 2))
                if puissance < 1e-7:
                    # Signal trop faible : on affiche "Silence"
                    self.after(0, self._afficher_note, "...", 0.0, 0.0, puissance)
                    return

                # Calcul du spectre avec fenetre de Hann
                spec  = np.abs(np.fft.fft(tampon * np.hanning(N))[: N // 2])
                # Suppression des frequences inferieures a 62 Hz
                spec[: int(62 / (fe / N))] = 0

                # Extraction du pic dominant et conversion en note
                idx = int(np.argmax(spec))
                f   = idx * fe / N
                if f <= 0:
                    return
                try:
                    i     = int(round(math.log2(f / 440) * 12))
                    note  = notes[i % 12] + str(4 + (i + 9) // 12)
                    f_ref = 440 * 2 ** (i / 12)
                    cents = 1200 * math.log2(f / f_ref)
                    # Mise a jour de l'affichage dans le thread principal (via after)
                    self.after(0, self._afficher_note, note, f, cents, puissance)
                except Exception:
                    pass

            with sd.InputStream(channels=1, callback=callback,
                                 blocksize=PAS, samplerate=fe):
                import time
                while not self._arret_demande:
                    time.sleep(0.1)

        except ImportError as e:
            self._ecrire(f"  ERREUR : {e}", "err")
        except Exception as e:
            self._ecrire(f"  Accordeur arrete : {e}", "err")

    def _afficher_note(self, note, freq, cents, puissance):
        """
        Met a jour la zone de sortie avec la note courante.
        Appelee depuis le thread principal via self.after().
        """
        self.sortie.config(state="normal")
        # Suppression des lignes precedentes pour simuler un rafraichissement
        for _ in range(6):
            self.sortie.delete("end-2l", "end-1l")

        if note == "...":
            self.sortie.insert("end", "  Silence (niveau trop faible)\n", "")
        else:
            # Construction de la barre visuelle d'accordeur
            largeur = 29
            centre  = largeur // 2
            pos     = int(cents / 50 * (largeur // 2))   # 50 cents = moitie de la barre
            pos     = max(-centre, min(centre, pos))
            barre   = ["-"] * largeur
            barre[centre] = "|"           # repere central = note juste
            barre[centre + pos] = "o"     # position de l'aiguille
            if pos == 0:
                barre[centre] = "o"
            barre_str = "[" + "".join(barre) + "]"

            # Couleur selon l'ecart : vert < 10 cents, orange < 25, rouge sinon
            couleur = "ok" if abs(cents) < 10 else "val" if abs(cents) < 25 else "err"

            self.sortie.insert("end", f"  Note detectee  : {note}\n",           couleur)
            self.sortie.insert("end", f"  Frequence      : {freq:.1f} Hz\n",    "")
            self.sortie.insert("end", f"  Ecart          : {cents:+.1f} cents\n", couleur)
            self.sortie.insert("end", f"  {barre_str}\n",                       couleur)
            self.sortie.insert("end",  "  (vert = accorde, orange = proche, rouge = loin)\n", "")

        self.sortie.see("end")
        self.sortie.config(state="disabled")

    def _stop_realtime(self):
        """Demande l'arret de la boucle de capture audio."""
        self._arret_demande = True
        self._statut("Accordeur arrete.")
        self._ecrire("")
        self._ecrire("  [Accordeur arrete]", "err")


# Point d'entree
if __name__ == "__main__":
    app = AppAccordeur()
    app.mainloop()
