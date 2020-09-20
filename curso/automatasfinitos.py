import abc
import itertools
from typing import Collection, Hashable, NamedTuple

Estado = Hashable
Simbolo = str


class TripletaDeTransicion(NamedTuple):
    estado: Estado
    simbolo: Simbolo
    siguiente_estado: Estado


class AutomataFinito(abc.ABC):
    @property
    @abc.abstractmethod
    def estado_inicial(self) -> Estado:
        raise NotImplementedError()

    @abc.abstractmethod
    def transicion(self, estado: Estado, simbolo: str) -> Estado:
        raise NotImplementedError()

    @abc.abstractmethod
    def es_de_aceptacion(self, estado: Estado) -> bool:
        raise NotImplementedError()

    def __call__(self, entrada: str) -> bool:
        estado = self.estado_inicial
        for simbolo in entrada:
            estado = self.transicion(estado, simbolo)
        return self.es_de_aceptacion(estado)

    correr = __call__


class AutomataFinitoDeterminista(AutomataFinito):
    def __init__(self, transiciones: Collection[TripletaDeTransicion],
                 inicial: Estado, aceptacion: Collection[Estado]):
        self._estados_de_aceptacion = set(aceptacion)
        self._estado_inicial = inicial
        self._transicion = {(q, s): r for (q, s, r) in transiciones}
        self._validar()

    def _validar(self):
        estados = {q for q, s in self._transicion}  # Calcular Q
        estados.update(self._transicion.values())  # Im(δ) ⊆ Q
        estados.update(self._estados_de_aceptacion)  # F ⊆ Q
        estados.add(self._estado_inicial)  # q₀ ∈ Q

        alfabeto = {s for q, s in self._transicion}  # Calcular Σ

        dominio = self._transicion.keys()
        for par in itertools.product(estados, alfabeto):
            if par in dominio:
                continue
            raise ValueError(f'Transición indefinida para {par!r}.')

    def estado_inicial(self) -> Estado:
        return self._estado_inicial

    def transicion(self, estado: Estado, simbolo: str) -> Estado:
        return self._transicion[estado, simbolo]
