from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs

@dataclass
class NFA[STATE]:
    # Alfabetul
    S: set[str]
    # Multimea de stari
    K: set[STATE]
    # Starea initiala
    q0: STATE
    # Functia de tranzitie
    d: dict[tuple[STATE, str], set[STATE]]
    # Multimea starilor finale
    F: set[STATE]

    # Calculam inchiderea epsilon a unei stari
    def epsilon_closure(self, state: STATE) -> set[STATE]:
        # Incepem stiva doar cu starea pe care vrem sa calculam inchiderea epsilon
        stack = [state]
        # Multimea rezultat, orice stare apartine propriei inchideri epsilon
        closure = {state}
        # Cat timp mai sunt stari in stiva
        while stack:
            # Scoatem ultima stare adaugata
            s = stack.pop()
            # Parcurgem toate destinatiile starii s prin tranzitii epsilon
            for t in self.d.get((s, EPSILON), set()):
                # Daca t nu se afla deja in inchidere
                if t not in closure:
                    # TODO
                    closure.add(t)
                    # Si o punem pe stiva
                    stack.append(t)
        # Returnam starile accesibile
        return closure

    # Algorithmul de transformare NFA intr-un dfa
    def subset_construction(self) -> DFA[frozenset[STATE]]:
        # Importam local clasa DFA
        from .DFA import DFA

        # Luam alfabetul NFA-ului, eliminand tranzitia epsilon
        alphabet = set(self.S)
        if EPSILON in alphabet:
            alphabet.remove(EPSILON)

        # Luam un set de stari si returnam starile pe care setul le poate atinge cu epsilon
        def eclosure_set(states: set) -> set:
            # Multimea finala
            res = set()
            # Stiva pentru lista
            stack = list(states)
            # Cat timp avem in stiva
            while stack:
                # Scoatem din stiva
                s = stack.pop()
                # Verificam daca este deja in rezultat
                if s not in res:
                    # Daca nu este il adaugam
                    res.add(s)
                    # Parcurgem toate destinatiile
                    for t in self.d.get((s, EPSILON), set()):
                        # Daca nu este in res
                        if t not in res:
                            # Il adaugam in stiva
                            stack.append(t)
            # Returnam rezultatul
            return res

        # Calculculam inchiderea epsilon a starii initiale
        start_closure = tuple(sorted(eclosure_set({self.q0}), key=str))
        # Multimea de stari a DFA-ului
        D_states = {start_closure}
        # Starea initiala a DFA-ului
        D_q0 = start_closure
        # Multimea starilor finale
        D_F = set()
        # Functia de tranzitie a DFA-ului
        D_d = {}

        # Lista de stari DFA neprocesate
        unmarked = [start_closure]
        # Cat timp exista stari
        while unmarked:
            # Luam o stare neprocesata
            T = unmarked.pop()
            # Verificam daca este stare finala
            is_final = False
            for s in T:
                if s in self.F:
                    is_final = True
                    break
            # Daca este stare finala, o adaugam
            if is_final:
                D_F.add(T)
            # Pentru fiecare simbol din alfabet
            for a in alphabet:
                # Multimea starilor NFA inaccesibile
                move = set()
                for s in T:
                    # Adugam fiecare stare destinatie
                    for t in self.d.get((s, a), set()):
                        move.add(t)
                # Inchiderea epsilon a multimii rezultate
                U_set = eclosure_set(move)
                # Eticheta determinista pentru multime
                U = tuple(sorted(U_set, key=str))
                # Definim tranzitia DFA
                D_d[(T, a)] = U
                # Daca U este o stare noua in DFA, o adaugam
                if U not in D_states:
                    D_states.add(U)
                    unmarked.append(U)
        # returnam DFA-ul
        return DFA(alphabet, set(D_states), D_q0, D_d, set(D_F))

    # Functia pentru refacerea starilor
    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'NFA[OTHER_STATE]':
        # Creeam o copie a NFA-ului
        new = NFA()
        # Copiem alfabetul
        new.S = set(self.S)
        # Aplicam f pentru a transforma fiecare stare in multimea K
        new.K = set(map(f, self.K))
        # Transformam starea initiala
        new.q0 = f(self.q0)
        # Transformam starile finale
        new.F = set(map(f, self.F))
        # Construim noua functie de tranzitie
        new.d = {}
        for key in list(self.d.keys()):
            s, a = key
            dests = self.d[key]
            new_key = (f(s), a)
            new.d[new_key] = set(map(f, dests))
        return new