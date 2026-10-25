# Slide deck

1. Apri `presentation_editor.html` in Chrome o Edge.
2. Scegli la cartella `presentation` (la radice del deck, non la singola sottocartella).

L'editor legge da solo le sottocartelle, in ordine naturale (`1/`, `2/`, `2.2/`, `3/`, ...),
e mette tutte le slide in un'unica sequenza: la prima slide di `2/` è la 16, la seconda di
`2/2/` è la 17, e cosi via. Il contatore in Present e quello della lista usano questo numero
globale, mentre dentro ogni cartella i file restano numerati da `01` per conto loro; i
pulsanti su/giu spostano una slide solo dentro il suo capitolo e rinumerano quella cartella.

La cartella scelta viene ricordata: alla riapertura l'editor la riprende da solo; se il
browser richiede di nuovo il permesso compare `Riprendi <nome>` e basta un clic.

Ogni capitolo (cartella) ha il suo `slideui.css` e `slideui.js`: anteprima, Present ed
Export inlinano quelli della cartella a cui appartiene la slide, quindi due moduli possono
avere framework e stili diversi nello stesso deck. Se una cartella non ha i suoi file,
l'editor risale alle cartelle genitori e infine al framework di base.

In Present le slide si cambiano con una dissolvenza; `Esc` chiude e `F` porta l'app a
schermo intero (di nuovo `F`, o `Esc`, per uscire).
