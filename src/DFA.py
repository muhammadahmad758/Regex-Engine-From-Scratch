from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
import pandas as pd
from typing import TypeVar
from functools import reduce

STATE = TypeVar('STATE')
OTHER = TypeVar('OTHER')

@dataclass
class DFA[STATE]:
    # Alfabetul reprezentat ca multime de caractere
    S: set[str]
    # Multimea starilor
    K: set[STATE]
    # Starea initiala
    q0: STATE
    # Functia de tranzitie
    d: dict[tuple[STATE, str], STATE]
    # Multimea starilor acceptate/finale
    F: set[STATE]
    
    # Verifica daca cuvantul este acceptat de DFA
    def accept(self, word: str) -> bool:
        # Parcurgem cuvantul caracter cu caracter, urmand tranzitiile DFA-ului
        cur = self.q0
        for ch in word:
            # Daca nu exista o tranzitie definita pentru perechea (stare curenta, caracter),
            # inseamna ca cuvantul nu este acceptat
            if (cur, ch) not in self.d:
                return False
            # Mergem la starea urmatoare conform functiei de tranzitie
            cur = self.d[(cur, ch)]
        # Dupa procesarea intregului cuvant, verificam daca starea curenta este una finala
        return cur in self.F
    

    def minimize(self) -> 'DFA[STATE]':
        # Algoritmul lui Hopcroft
        # K: copii ale multimii starilor
        K = set(self.K)
        # stari finale si nefinale
        F = set(self.F)
        nonF = K - F

        # Lista partitiilor
        P = []
        #Daca exista stari finale, le adaugam ca o partitie
        if F:
            P.append(set(F))
        #Daca exista stari nefinale, le adaugam ca o partitie
        if nonF:
            P.append(set(nonF))

        # Coada de lucru pentru Hopcroft
        if F:
            W = [set(F)]
        else:
            W = []

        steps = 0
        splits = 0

        # Alfabetul pentru tranzitii
        alphabet = set(self.S)

        # Cat timp lista nu este vida
        while W:
            # Preluam o partitie din coada
            A = W.pop()
            # Pentru fiecare caracter din alfabet
            for c in alphabet:
                # Incrementam contorul de pasi
                steps += 1
                # Multumea starilor care tranzitioneaza in A pe c
                # X = {q | d(q,c) in A}
                X = set()
                for q in K:
                    dest = self.d.get((q,c), None)
                    if dest in A:
                        X.add(q)

                # Refinam partitiile din P folosind X
                newP = []
                for Y in P:
                    # Calculam intersectia si diferenta
                    inter = Y & X
                    diff = Y - X
                    # Daca ambele nu sunt vide
                    if inter and diff:
                        # Spargem Y in inter si diff
                        splits += 1
                        newP.append(inter)
                        newP.append(diff)
                        # Daca Y era in cuvant
                        if Y in W:
                            # Este inlocuit cu cele 2 blocuri
                            W.remove(Y)
                            W.append(inter)
                            W.append(diff)
                        # Altfel adaugam in W pe cel mai mic
                        else:
                            if len(inter) <= len(diff):
                                W.append(inter)
                            else:
                                W.append(diff)
                    # Daca nu se sparge pastram Y ca atare
                    else:
                        newP.append(Y)
                # P primeste newP
                P = newP

        # Construim noul DFA din partitia P
        block_of = {}
        new_states = set()
        for block in P:
            # Folosim tuple sortat ca reprezentant al blocului
            fb = tuple(sorted(block, key=str))
            # Setam noua stare ca fiind acest reprezentant
            new_states.add(fb)
            # Mapam fiecare stare originala la blocul sau reprezentant
            for q in block:
                block_of[q] = fb

        # Construim noul DFA minimizat
        new_q0 = block_of[self.q0]
        # Construim multimea starilor finale in noul DFA: un bloc este final
        # daca cel putin una din starile sale componente este finala in vechiul DFA.
        new_F = set()
        for b in new_states:
            for s in b:
                if s in self.F:
                    new_F.add(b)
                    break
        # Construim functia de tranzitie pentru noul DFA
        new_d = {}
        for b in new_states:
            # Luam orice reprezentant al blocului
            rep = next(iter(b))
            # Luam fiecare caracter din alfabet
            for c in alphabet:
                dest = self.d.get((rep, c), None)
                if dest is None:
                    # tranzitie nedefinita: pastram ca None
                    new_d[(b, c)] = None
                else:
                    new_d[(b, c)] = block_of[dest]

        # Cream noul DFA minimizat
        new_dfa = DFA(self.S, new_states, new_q0, new_d, new_F)
        # Atacham statistici
        setattr(new_dfa, '_hopcroft_steps', steps)
        setattr(new_dfa, '_hopcroft_splits', splits)
        return new_dfa
    
    # Remapeaza starile DFA folosind functia f
    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'DFA[OTHER_STATE]':
        # Construim noile componente ale DFA-ului remapat
        new_K = set(map(f, self.K))
        new_q0 = f(self.q0)
        new_F = set(map(f, self.F))
        new_d = {}
        for (s, c), dest in self.d.items():
            new_d[(f(s), c)] = f(dest)
        # Returnam noul DFA remapat
        return DFA(self.S, new_K, new_q0, new_d, new_F)
    
    