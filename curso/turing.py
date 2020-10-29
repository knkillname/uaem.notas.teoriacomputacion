import collections
import enum
from typing import Collection, Dict, Hashable, NamedTuple, Optional, Sequence, Tuple

Estado = Hashable
Símbolo = str


class Dirección(int, enum.Enum):
    IZQUIERDA = -1
    NINGUNA = 0
    DERECHA = 1


class Transición(NamedTuple):
    estado: Estado
    leer: Símbolo
    siguiente: Estado
    escribir: Símbolo
    mover: int


Programa = Collection[Transición]


class Cinta:
    def __init__(self, entrada: str = '', blanco: str = ' ',
                 posición: int = 0) -> None:
        self._blanco = blanco
        self.reiniciar(entrada)
        self.mover(posición)

    def mover(self, dirección: int) -> None:
        self.posición += dirección

    @property
    def contenido(self) -> Sequence[Símbolo]:
        if all(isinstance(s, str) and len(s) == 1 for s in self._contenido):
            return ''.join(self._contenido)
        return list(self._contenido)

    @property
    def blanco(self) -> Símbolo:
        return self._blanco

    @property
    def posición(self) -> int:
        return self._posición

    @posición.setter
    def posición(self, valor):
        if not isinstance(valor, int):
            raise TypeError()
        valor = max(valor, 0)
        if valor >= (longitud := len(self.contenido)):
            faltantes = valor - longitud + 1
            self._contenido += [self.blanco]*faltantes
        self._posición = valor

    def leer(self) -> Símbolo:
        return self._contenido[self.posición]

    def escribir(self, símbolo: Símbolo) -> None:
        self._contenido[self.posición] = símbolo

    def reiniciar(self, entrada: str = ''):
        self._contenido = list(entrada) if entrada else [self.blanco]
        self.posición = 0

    def __repr__(self) -> str:
        kwargs = {}
        if (contenido := self.contenido):
            kwargs['contenido'] = contenido
        if (self.blanco) != ' ':
            kwargs['blanco'] = self.blanco
        if self.posición != 0:
            kwargs['posición'] = self.posición
        args = ', '.join(f'{key}={value!r}' for key, value in kwargs.items())
        return f'{self.__class__.__name__}({args})'


class MáquinaDeTuring:
    def __init__(self, programa: Programa, aceptación: Estado,
                 blanco: str = ' ') -> None:
        self._blanco = blanco
        self._función_de_transición = self._programa_a_función(programa)
        self._aceptación = aceptación

    def _programa_a_función(self, programa) \
            -> Dict[Tuple[Estado, Símbolo], Tuple[Estado, Símbolo, int]]:
        programa = tuple(programa)
        resultado = {
            (estado, leer): (siguiente, escribir, mover)
            for (estado, leer, siguiente, escribir, mover) in programa}

        if len(resultado) < len(programa):
            cuenta = collections.Counter((estado, leer)
                                         for estado, leer, _, _, _ in programa)
            par = cuenta.most_common(1)[0][0]
            raise ValueError(f'Más de una transición definida para {par}.')

        return resultado

    @property
    def programa(self):
        resultado = []
        for transición in self._función_de_transición.items():
            (estado, leer), (siguiente, escribir, mover) = transición
            resultado.append(
                Transición(estado, leer, siguiente, escribir, mover))
        return resultado
