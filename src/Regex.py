from .NFA import NFA

# Epsilon
EPSILON = ''

# Clasa de baza pentru nodurile AST ale regexului
class RegexBase:
    def thompson(self) -> NFA[int]:
        # Fiecare clasa returneaza un NFA contruit prin Thompson
        raise NotImplementedError()

# Nod pentru un caracter simplu
class Char(RegexBase):
    def __init__(self, ch: str):
        self.ch = ch

    def thompson(self) -> NFA:
        # Construim un NFA minimal care recunoaste exact caracterul self.ch
        # Dictionar pentru functia de tranzitii
        d = {}
        # Definim o tranzitie din starea 0 spre starea 1
        d[(0, self.ch)] = {1}
        # Returnam NFA-ul construit
        return NFA({self.ch}, {0,1}, 0, d, {1})


class CharClass(RegexBase):
    def __init__(self, chars: set[str]):
        # Salvam multimea de caractere care definesc clasa
        self.chars = set(chars)

    # Construim functia de tranzitie pentru NFA
    def thompson(self) -> NFA:
        # Dictionarul pentru functia de tranzitie
        d = {}
        # Pentru fiecare caracter din clasa curenta
        for ch in self.chars:
            # Cream un set clasic in caz ca, cheia nu exista
            d.setdefault((0, ch), set()).add(1)
        # Returnam noul NFA
        return NFA(set(self.chars), {0, 1}, 0, d, {1})


class Concat(RegexBase):
    def __init__(self, left: RegexBase, right: RegexBase):
        self.left = left
        self.right = right

    def thompson(self) -> NFA:
        # Construim NFA-ul pentru sub-expresiile de stanga si dreapta
        n1 = self.left.thompson()
        n2 = self.right.thompson()
        # Calculam un offset pentru a reindexa starile lui n
        # Coliziuni cu n1
        offset = max(n1.K) + 1 if len(n1.K) else 1
        # Functiile de tranzitie
        d = {}
        # Copiem toate tranzitiile in noul dictionar
        for key in list(n1.d.keys()):
            s, c = key
            dests = n1.d[key]
            d[(s, c)] = set(dests)

        # Din fiecare stare finala a lui n1 adaugam o tranzitie epsilon catre n2
        for f in n1.F:
            d.setdefault((f, EPSILON), set()).add(n2.q0 + offset)

        # opiem tranzitiile lui n2 reindexate cu offsetul
        for key in list(n2.d.keys()):
            s, c = key
            dests = n2.d[key]
            ns = s + offset
            ndests = {t + offset for t in dests}
            d[(ns, c)] = ndests
        
        # Construim multimea totala de stari
        K = set(n1.K)
        for s in n2.K:
            K.add(s + offset)
        # Alfabetul rezultat este reuniunea alfabetelor ambelor sub-NFA-uri
        S = set(n1.S)
        for ch in n2.S:
            S.add(ch)
        # Starea initiala a concatenarii este starea initiala a lui n1
        q0 = n1.q0
        # Starile final
        F = {t + offset for t in n2.F}
        # Returnam NFA-ul concatenat
        return NFA(S, K, q0, d, F)


class Union(RegexBase):
    def __init__(self, left: RegexBase, right: RegexBase):
        self.left = left
        self.right = right

    def thompson(self) -> NFA:
        # Constuim NFA-urile pentru subexpresiile stanga si dreapta
        n1 = self.left.thompson()
        n2 = self.right.thompson()
        
        # Calculam offset-ul pentru a reindexa starile astfel incat sa nu existe coliziuni
        o1 = max(n1.K) + 1 if len(n1.K) else 1
        o2 = o1 + max(n2.K) + 1 if len(n2.K) else o1 + 1
        # Vom folosi o stare noua de start (0)
        start = 0
        # Reindexam n1 incepand de la base1 = 1
        base1 = 1
        d = {}
        # Copiem toate tranzitiile lui n1 in d
        for key in list(n1.d.keys()):
            s, c = key
            dests = n1.d[key]
            d[(s + base1, c)] = {t + base1 for t in dests}

        # Plasam n2 dupa n1
        base2 = base1 + max(n1.K) + 1

        # Copiem tranzitiile lui n2
        for key in list(n2.d.keys()):
            s, c = key
            dests = n2.d[key]
            d[(s + base2, c)] = {t + base2 for t in dests}

        # Stabilim noul start si noul accept
        new_start = start
        new_accept = base2 + max(n2.K) + 1

        # Adaugam tranzitii epsilon din noul start catre starturile reindexate
        d.setdefault((new_start, EPSILON), set()).add(n1.q0 + base1)
        d.setdefault((new_start, EPSILON), set()).add(n2.q0 + base2)
        
        # Din finalele fiecarui sub-NFA adaugam epsilon catre nou accept
        for f in n1.F:
            d.setdefault((f + base1, EPSILON), set()).add(new_accept)
        for f in n2.F:
            d.setdefault((f + base2, EPSILON), set()).add(new_accept)
            
        # Alfabetul rezultat este reuniunea alfabetelor ambelor sub-NFA-uri
        S = set(n1.S)
        for ch in n2.S:
            S.add(ch)
        
        # Multimea de stari incluzand noul start, noul accept si toate starile reindexate
        K = set()
        K.add(new_start)
        K.add(new_accept)
        for s in n1.K:
            K.add(s + base1)
        for s in n2.K:
            K.add(s + base2)
        # Returnam NFA-ul
        return NFA(S, K, new_start, d, {new_accept})


class Star(RegexBase):
    def __init__(self, expr: RegexBase):
        self.expr = expr

    def thompson(self) -> NFA:
        # Construim NFA-ul pentru expresia de baza A
        n = self.expr.thompson()
        # Mutam intregul NFA cu un offset pentru a face loc noilor stari
        base = 1
        
        # Dictionarul de tranzitii pentru noul NFA
        d = {}
        
        # Reindexam toate tranzitiile din NFA-ul original
        for key in list(n.d.keys()):
            s, c = key
            dests = n.d[key]
            d[(s + base, c)] = {t + base for t in dests}
        
        # Noua stare de start va fi 0
        new_start = 0
        # Noua stare de accept este dupa toate starile reindexate
        new_accept = max(n.K) + base + 1
        # Tranzitie epsilon de la noul start la startul expresiei
        d.setdefault((new_start, EPSILON), set()).add(n.q0 + base)
        # Tranzitia epsilon de la noul start la noua stare finala
        d.setdefault((new_start, EPSILON), set()).add(new_accept)

        # Pentru fiecare stare finala din expresia originala ii setam noua tranzitie
        for f in n.F:
            d.setdefault((f + base, EPSILON), set()).add(n.q0 + base)
            d.setdefault((f + base, EPSILON), set()).add(new_accept)

        # Alfabetul ramane acelasi ca la expresia originala
        S = set(n.S)
        
        # Construim multimea strailor noului NFA
        K = set()
        K.add(new_start)
        K.add(new_accept)
        for s in n.K:
            K.add(s + base)

        # Returnam NFA
        return NFA(S, K, new_start, d, {new_accept})

# Salvam expresia asupra careia aplicam operatorul +
class Plus(RegexBase):
    def __init__(self, expr: RegexBase):
        self.expr = expr

    # Consruim un NFA pentru concatenarea dintre A si A*
    def thompson(self) -> NFA:
        # Extragem expresia de baza
        a = self.expr
        # Concatenam folosind functiile declarate mai sus
        return Concat(a, Star(a)).thompson()


# Salvam expresia supra careia paplicam operatorul ?
class Optional(RegexBase):
    def __init__(self, expr: RegexBase):
        self.expr = expr
    
    # A? = A | epsilon
    def thompson(self) -> NFA:
        # Construim o uniune intre expresie si epsilon
        return Union(self.expr, CharClass({EPSILON})).thompson()


# Parser recursiv pentru expresiile regulate
def parse_regex(s: str) -> RegexBase:
    i = 0

    # Returnam caracterul curent fara a avansa cursorul
    def peek():
        return s[i] if i < len(s) else None

    # Returnam caracterul curent si avansam cursorul cu 1
    # Este folosit pentru consumul efectiv al unui token cand stim ca exista
    def next_char():
        nonlocal i
        if i >= len(s):
            return None
        ch = s[i]
        i += 1
        return ch

    # Parsam o clasa de caractere intre '[' si ']'
    def parse_class() -> CharClass:
        nonlocal i
        # Caracterul curent este '['
        chars = set()
        assert s[i] == '['
        # Consumam '['
        i += 1
        
        # Parcurgem pana la intalnirea caracterului ']'
        while i < len(s) and s[i] != ']':
            # Verificam daca avem un interval de forma a-z
            if i + 2 < len(s) and s[i+1] == '-':
                # Prima si ultima litera din interval
                a = s[i]
                b = s[i+2]
                # Adaugam toate caracterele din interval in multime
                for code in range(ord(a), ord(b) + 1):
                    chars.add(chr(code))
                # Sarim peste secventa a-b
                i += 3
            else:
                # Verificam daca avem un caracter capadt cu backslash
                if s[i] == '\\':
                    # Sarim peste '\'
                    i += 1
                    # Daca exista un caracter dupa \
                    if i < len(s):
                        # Luam caracterul
                        esc = s[i]
                        # Interpretam secventa
                        if esc == 'n':
                            chars.add('\n')
                        elif esc == 't':
                            chars.add('\t')
                        else:
                            # Altfel il tratam ca pe un caracter normal
                            chars.add(esc)
                        # Avansam
                        i += 1
                # Altfel plasam caracterul obisnuit
                else:
                    chars.add(s[i])
                    i += 1
        # Trecem peste ]
        if i < len(s) and s[i] == ']':
            i += 1
        # Returnam noul CharClass care contine multimea de caractere
        return CharClass(chars)

    # Parseaza un "atom" care este unitatea de baza
    def parse_atom():
        nonlocal i
        # Sarim peste spatiile ne-escapate
        while i < len(s) and s[i] == ' ':
            i += 1
        # Daca am ajuns la sfarsitul sirului, nu mai avem atom
        if i >= len(s):
            return None
        # Caracterul curent
        ch = s[i]
        # Expresii intre paranteze
        if ch == '(':
            i += 1
            # Delegam catre parse_union
            node = parse_union()
            if i < len(s) and s[i] == ')':
                i += 1
            # returnam expresia intre ()
            return node
        # Delegam catre parse_class
        if ch == '[':
            return parse_class()
        # Daca avem \\ verificam sa nu fie \n, \t, etc
        if ch == '\\':
            i += 1
            if i < len(s):
                esc = s[i]
                i += 1
                if esc == 'n':
                    return Char('\n')
                if esc == 't':
                    return Char('\t')
                return Char(esc)
            return None
        # Daca | si ) nu pot fi atomi
        if ch in ['|', ')']:
            return None
        # Daca am ajuns aici, este un aracter normal
        i += 1
        return Char(ch)

    # Parsam un factor care poate avea operatorii *,+,?
    def parse_repeat():
        nonlocal i
        # Parsam elementul de baza
        node = parse_atom()
        #Daca nu avem atom, nu avem repetare
        if node is None:
            return None
        # Verificam daca atomul este urmat de unul dintre operatorii postifxati
        while i < len(s) and s[i] in ['*', '+', '?']:
            op = s[i]
            # Consumam operatorul
            i += 1
            #Verificam ce tip este si il trimitem spre functia repsectiva
            if op == '*':
                node = Star(node)
            elif op == '+':
                node = Plus(node)
            elif op == '?':
                node = Optional(node)
        return node

    # Parsam o concatenare implicaita, secventa de factori care apar unul dupa altul
    def parse_concat():
        nonlocal i
        # Lista de noduri care vor fi concatenate
        parts = []
        while True:
            # Trecem peste caracterele spatiu
            while i < len(s) and s[i] == ' ':
                i += 1
            # Stopam la sfarsitul de sir sau cand intalnim ) sau |
            if i >= len(s) or s[i] == ')' or s[i] == '|':
                break
            # Parsam urmatorul element prin repetare cu eventuali operatori
            part = parse_repeat()
            if part is None:
                break
            # Adaugam nodul in lista
            parts.append(part)
        # Daca nu s-a gasit niciun element, returnam epsilon
        if not parts:
            return CharClass({EPSILON})
        # Construim nodul Concat pentru toate elementele din lista
        node = parts[0]
        for p in parts[1:]:
            node = Concat(node, p)
        # Returnam nodul concatenta
        return node

    # Parsam alternarea introducand noduri Union pentru fiecare |
    def parse_union():
        nonlocal i
        # Parsam prima secventa de concatenari
        node = parse_concat()
        while True:
            # Trecem peste caracterul spatiu
            while i < len(s) and s[i] == ' ':
                i += 1
            # Daca gasim operatorul |
            if i < len(s) and s[i] == '|':
                i += 1
                # Parsam partea dreapta a uniunii
                right = parse_concat()
                # Construim nodul
                node = Union(node, right)
            else:
                break
        return node
    
    # Construim AST-ul complet
    root = parse_union()
    # Il returnam
    return root

        