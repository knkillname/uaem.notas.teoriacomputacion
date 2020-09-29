"""
Clases base para autómatas finitos.
"""
import abc
import collections
import functools
import itertools
import json
import pathlib
from typing import Any, Collection, Dict, FrozenSet, Hashable, Iterable, Mapping, NamedTuple, Set, Tuple, Type, TypeVar, Union

Estado = Hashable
Simbolo = str
_T = TypeVar('_T')


class Transicion(NamedTuple):
    """
    Define una transición de estado en un autómata finito.
    """
    estado: Estado
    simbolo: Simbolo
    siguiente: Estado


Programa = Collection[Transicion]


class AutomataFinito(abc.ABC):
    """
    Clase base abstracta para los autómatas finitos.
    """

    def __init__(
            self,
            programa: Programa,
            estado_inicial: Estado,
            estados_de_aceptacion: Collection[Estado]):
        self._estados_de_aceptacion = set(estados_de_aceptacion)
        self._estado_inicial = estado_inicial

        self._transicion = self._programa_a_funcion(programa)
        self._validar()

    @abc.abstractmethod
    def _validar(self) -> None:
        """
        Produce un error si el autómata se encuentra mal definido.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _programa_a_funcion(cls, programa: Programa) -> Any:
        raise NotImplementedError()
    
    @property
    @abc.abstractmethod
    def programa(self) -> Programa:
        raise NotImplementedError()

    @property
    def estado_inicial(self) -> Estado:
        """
        El estado inicial del autómata.
        """
        return self._estado_inicial
    
    @property
    def estados_de_aceptacion(self) -> Collection[Estado]:
        return frozenset(self._estados_de_aceptacion)
        
    
    @functools.cached_property
    def alfabeto(self) -> Collection[Simbolo]:
        return frozenset(simbolo
                         for estado, simbolo, siguiente in self.programa
                         if simbolo)
    
    @functools.cached_property
    def estados(self) -> Collection[Estado]:
        resultado = {self.estado_inicial}
        resultado.update(self._estados_de_aceptacion)
        resultado.update(estado
                         for estado, simbolo, siguiente in self.programa)
        resultado.update(siguiente 
                         for estado, simbolo, siguiente in self.programa)
        return frozenset(resultado)

    @abc.abstractmethod
    def transicion(self, estado: Estado, simbolo: str) \
            -> Union[Estado, Collection[Estado]]:
        """
        Función de transición.

        Parámetros
        ----------
        estado: El estado actual del autómata.

        simbolo: El símbolo actual que se está consumiendo de la
            entrada. 
        """
        raise NotImplementedError()

    def es_de_aceptacion(self, estado: Estado) -> bool:
        """
        Determina si el estado es de aceptación o no.
        """
        return estado in self.estados_de_aceptacion

    @abc.abstractmethod
    def __call__(self, entrada: str) -> bool:
        """
        Corre el autómata ante una cadena de entrada y determina si la
        cadena es o no aceptada.
        """
        raise NotImplementedError()

    def guardar(self, archivo: pathlib.Path):
        """
        Guarda el autómata finito en un archivo de texto en formato JSON.
        """
        obj = {
            'programa': [transicion._asdict()
                         for transicion in self.programa],
            'estado_inicial': self._estado_inicial,
            'estados_de_aceptacion': list(self._estados_de_aceptacion)
        }
        with archivo.open('w', encoding='utf8') as fp:
            json.dump(obj, fp, indent=2, ensure_ascii=False)

    @classmethod
    def abrir(cls: Type[_T], archivo: pathlib.Path) -> _T:
        """
        Lee el autómata finito desde un archivo de texto en formato JSON.
        """
        with archivo.open(encoding='utf8') as fp:
            obj = json.load(fp)
        obj['programa'] = [Transicion(**registro)
                           for registro in obj['programa']]
        return cls(**obj)


class AFD(AutomataFinito):
    @classmethod
    def _programa_a_funcion(cls, programa: Programa) \
            -> Dict[Tuple[Estado, Simbolo], Estado]:
        dominio = collections.Counter((q, s) for (q, s, r) in programa)
        par, repeticiones = dominio.most_common(1)[0]
        if repeticiones > 1:
            raise ValueError('Programa mal formado: hay dos o más '
                             f'trancisiones posibles para {par!r}.')
        return {(q, s): r for (q, s, r) in programa}
    
    @functools.cached_property
    def programa(self) -> Programa:
        return tuple(Transicion(q, s, r)
                     for (q, s), r in self._transicion.items())

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

    def transicion(self, estado: Estado, simbolo: str) -> Estado:
        try:
            return self._transicion[estado, simbolo]
        except KeyError:
            if estado not in {q for (q, s) in self._transicion}:
                raise KeyError(f'{estado!r} no es un estado del autómata.')
            raise KeyError(f'{simbolo!r} no es parte del alfabeto.')

    def __call__(self, entrada: str) -> bool:
        estado = self.estado_inicial
        for simbolo in entrada:
            estado = self.transicion(estado, simbolo)
        return self.es_de_aceptacion(estado)


class AFN(AutomataFinito):
    def _validar(self):
        pass  # TODO: ¿Hay algo que validar?

    @classmethod
    def _programa_a_funcion(cls, programa: Programa) \
            -> Dict[Estado, Dict[Simbolo, FrozenSet[Estado]]]:
        resultado = {}
        for estado, simbolo, siguiente in programa:
            resultado.setdefault(estado, {})\
                .setdefault(simbolo, set()).add(siguiente)
        for estado, vecinos in resultado.items():
            for simbolo, siguientes in vecinos.items():
                vecinos[simbolo] = frozenset(siguientes)
        return resultado
    
    @functools.cached_property
    def programa(self) -> Programa:
        resultado = []
        for estado, vecinos in self._transicion.items():
            for simbolo, siguientes in vecinos.items():
                for siguiente in siguientes:
                    resultado.append(Transicion(estado, simbolo, siguiente))
        return tuple(resultado)
    
    def cerradura_epsilon(self, estados: Iterable[Estado]) \
            -> Collection[Estado]:
        """
        Calcula el conjunto de estados a los que es posible llegar a
        partir de el conjunto de estados proporcionado usando sólo
        transiciones épsilon.
        """
        visitados = set(estados)
        cola = collections.deque(visitados)
        transicion = self._transicion
        while cola:
            estado = cola.popleft()
            for simbolo, siguientes in transicion.get(estado, {}).items():
                if simbolo: continue  # Si no es épsilon, continuar
                cola.extend(siguiente
                            for siguiente in siguientes
                            if siguiente not in visitados)
                visitados.update(siguientes)
        return visitados

    def transicion(self, estado: Estado, simbolo: str) -> FrozenSet[Estado]:
        try:
            return self._transicion[estado][simbolo]
        except KeyError:
            return frozenset()

    def __call__(self, entrada: str) -> bool:
        estados = self.cerradura_epsilon([self.estado_inicial])
        for simbolo in entrada:
            estados = {siguiente
                       for estado in estados
                       for siguiente in self.transicion(estado, simbolo)}
            estados = self.cerradura_epsilon(estados)
        return any(self.es_de_aceptacion(estado) for estado in estados)
