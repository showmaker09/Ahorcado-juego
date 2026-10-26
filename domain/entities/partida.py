from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Partida:
    """
    Entidad que representa el estado de la partida viva del juego.
    """
    id: str
    pista: str
    palabra_secreta: str
    espacios_visibles: List[str]
    letras_intentadas: List[str]
    vidas_restantes: int
    activo: bool
    ganador: Optional[str] = None

    @property
    def esta_activa(self) -> bool:
        """Determina si la partida está en curso y tiene vidas disponibles."""
        return self.activo and self.vidas_restantes > 0

    @property
    def es_victoria(self) -> bool:
        """Indica si la partida concluyó con un ganador registrado."""
        return not self.activo and bool(self.ganador) and "PERDIDOS" not in (self.ganador or "")

    @property
    def es_derrota(self) -> bool:
        """Indica si las vidas globales se han agotado."""
        return self.vidas_restantes <= 0 or (bool(self.ganador) and "PERDIDOS" in (self.ganador or ""))

    def contiene_letra(self, letra: str) -> bool:
        """Verifica si la letra forma parte de la palabra secreta."""
        return letra.strip().upper() in self.palabra_secreta.strip().upper()

    def ya_intentada(self, letra: str) -> bool:
        """Comprueba si la letra ya fue intentada por cualquier cliente."""
        letra_norm = letra.strip().upper()
        return any(l.strip().upper() == letra_norm for l in self.letras_intentadas)

    def calcular_nuevos_espacios(self, letra: str) -> List[str]:
        """
        Calcula la nueva lista de espacios visibles revelando todas las ocurrencias
        de la letra especificada.
        """
        letra_norm = letra.strip().upper()
        palabra_norm = self.palabra_secreta.strip().upper()

        nuevos = list(self.espacios_visibles)
        # Sincronizar longitud en caso de discrepancia
        if len(nuevos) != len(palabra_norm):
            nuevos = ['_' if c != ' ' else ' ' for c in palabra_norm]

        for i, char in enumerate(palabra_norm):
            if char == letra_norm:
                nuevos[i] = self.palabra_secreta[i].upper()
        return nuevos

    def esta_completada_con(self, espacios: List[str]) -> bool:
        """
        Verifica si los espacios visibles representan la palabra completa
        (sin caracteres '_' pendientes).
        """
        if '_' in espacios:
            return False
        return ''.join(espacios).strip().upper() == self.palabra_secreta.strip().upper()
