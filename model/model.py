#from UI.controller import Controller
from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi
        # Limiti scelti dall'utente per il pacchetto
        self._max_budget: float = None
        self._max_giorni: int = None

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        # Legge le coppie escursione-punto dalla tabella ponte
        relazioni = EscursioneDAO.get_escursioni_punti_interesse()

        if relazioni is None:
            return

        for rel in relazioni:
            id_escursione = rel['id_escursione']
            id_punto_interesse = rel['id_punto_interesse']

            # Recupera gli oggetti completi tramite i loro ID
            escursione = self.escursioni_map[id_escursione]
            punto_interesse = self.punti_interesse_map[id_punto_interesse]

            # Collega i due oggetti in entrambe le direzioni
            escursione.punti_interesse.add(punto_interesse)
            punto_interesse.escursioni.add(escursione)
        # TODO

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        # Azzera la soluzione calcolata in precedenza
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        # Salva le escursioni candidate e i limiti della nuova ricerca
        self.lista_escursioni_parco = []
        self._max_giorni = max_giorni
        self._max_budget = max_budget

        # Considera solo le escursioni del parco selezionato
        for escursione in self.escursioni_map.values():
            if escursione.id_parco == id_parco:
                self.lista_escursioni_parco.append(escursione)

        # Avvia la ricerca da un pacchetto inizialmente vuoto
        self._ricorsione(0, [], 0, 0, 0, set())


        # TODO

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""
        # 🟤 A - Istruzioni che dovrebbero essere sempre eseguite
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()

        # 🟢 B - if terminal_condition: do_something(...) -
        # Non necessaria perché ridondante

        for i in range(start_index, len(self.lista_escursioni_parco)):
            escursione = self.lista_escursioni_parco[i]
            # 🟡 C - if filter: ...
            # Se non c'è un limite di giorni oppure la nuova durata non lo supera
            if self._max_giorni is None or self._max_giorni >= (durata_corrente + escursione.durata_giorni):
                # Se non c'è un budget massimo oppure il nuovo costo non lo supera
                if self._max_budget is None or self._max_budget >= (costo_corrente + escursione.costo):
                    # intersection() trova i punti in comune tra i due set punti_usati e escursione.punti_interesse: con "not" deve essere vuota
                    if not punti_usati.intersection(escursione.punti_interesse):

                        # 🔵 D - compute_partial()

                        # Inserisce l'escursione nella combinazione corrente
                        pacchetto_parziale.append(escursione)

                        # Calcola la durata totale dopo l'aggiunta
                        new_durata = durata_corrente + escursione.durata_giorni

                        # Calcola il costo totale dopo l'aggiunta
                        new_costo = costo_corrente + escursione.costo

                        # Somma al valore corrente i voti dei punti dell'escursione
                        new_valore = valore_corrente + sum(punto.voto_visitatori for punto in escursione.punti_interesse)

                        # Registra tutti i punti dell'escursione come già usati
                        punti_usati.update(escursione.punti_interesse)

                        # 🔴 E - recursion(..., level + 1)
                        self._ricorsione(i+1, pacchetto_parziale, new_durata, new_costo, new_valore, punti_usati)

                        # 🟣 F - back_tracking()
                        # Rimuove l’ultima escursione aggiunta
                        pacchetto_parziale.pop()

                        # Rimuove i punti dell’escursione appena provata
                        punti_usati.difference_update(escursione.punti_interesse)
        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
