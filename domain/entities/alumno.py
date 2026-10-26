from dataclasses import dataclass


@dataclass(frozen=True)
class Alumno:
    """
    Entidad que representa a un alumno registrado en el sistema.
    Regla de negocio: La identidad está blindada; el nombre proviene
    exclusivamente del registro oficial de la base de datos.
    """
    matricula: str
    nombre_real: str

    @property
    def formato_ganador(self) -> str:
        """Formato oficial para registrar la victoria: 'NOMBRE REAL (MATRICULA)'."""
        return f"{self.nombre_real} ({self.matricula})"
