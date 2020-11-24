import enum
import functools
from typing import Collection, Dict, Hashable, NamedTuple, Sequence, Tuple

__all__ = ['Estado', 'Simbolo', 'Cinta', 'Movimiento', 'Transicion',
           'Programa', 'MaquinaDeTuring', ]

Estado = Hashable
Simbolo = str


class Cinta:
    def __init__(self, entrada: Sequence[Simbolo], blanco: Simbolo = ' '):
        self._blanco = blanco
        self._contenido = list(entrada) if entrada else [blanco]
        self._posicion = 0

    @property
    def posicion(self):
        return self._posicion

    @posicion.setter
    def posicion(self, valor: int):
        if not isinstance(valor, int):
            raise TypeError()
        valor = max(valor, 0)
        if valor >= (longitud := len(self._contenido)):
            faltan = valor - longitud + 1
            self._contenido += [self._blanco]*faltan
        self._posicion = valor

    def leer(self) -> Simbolo:
        return self._contenido[self.posicion]

    def escribir(self, simbolo: Simbolo):
        self._contenido[self.posicion] = simbolo

    def derecha(self):
        self.posicion += 1

    def izquierda(self):
        self.posicion -= 1


class Movimiento(int, enum.Enum):
    IZQUIERDA = -1
    NINGUNO = 0
    DERECHA = 1


class Transicion(NamedTuple):
    estado: Estado
    leer: Simbolo
    siguiente: Estado
    escribir: Simbolo
    mover: int


Programa = Collection[Transicion]


class MaquinaDeTuring:
    def __init__(self, programa: Programa, inicial: Estado,
                 finales: Collection[Estado], blanco: Simbolo = ' '):
        self._transicion = MaquinaDeTuring.programa_a_funcion(programa)
        self._inicial = inicial
        self._finales = frozenset(finales)
        self._blanco = blanco

    @property
    def blanco(self):
        return self._blanco

    @property
    def inicial(self):
        return self._inicial

    @property
    def finales(self):
        return self._finales

    @staticmethod
    def programa_a_funcion(programa) -> \
            Dict[Tuple[Estado, Simbolo], Tuple[Estado, Simbolo, int]]:

        return {(estado, simbolo): (siguiente, escribir, mover)
                for (estado, simbolo, siguiente, escribir, mover) in programa}

    @functools.cached_property
    def programa(self):
        pares = self._transicion.items()
        return tuple(
            (estado, leer, siguiente, escribir, mover)
            for ((estado, leer), (siguiente, escribir, mover)) in pares)

    @functools.cached_property
    def estados(self):
        resultado = {self.inicial}
        for (estado, simbolo, siguiente, escribir, mover) in self.programa:
            resultado |= {estado, siguiente}
        resultado |= self.finales
        return resultado

    @functools.cached_property
    def alfabeto(self):
        resultado = {self.blanco}
        for (estado, leer, siguiente, escribir, mover) in self.programa:
            resultado |= {leer, escribir}
        return resultado

    def __call__(self, palabra: Sequence[Simbolo]) -> bool:
        estado = self.inicial
        cinta = Cinta(palabra, blanco=self.blanco)
        while estado not in self.finales:
            leer = cinta.leer()
            tripleta = self._transicion.get((estado, leer))
            if tripleta is None:
                return False
            (estado, escribir, mover) = tripleta
            cinta.escribir(escribir)
            cinta.posicion += mover
        return True
