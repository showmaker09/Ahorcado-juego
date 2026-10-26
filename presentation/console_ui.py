import os
import sys
import time
from typing import Optional

from domain.entities.alumno import Alumno
from domain.entities.partida import Partida
from application.use_cases.validar_matricula import ValidarMatriculaUseCase
from application.use_cases.verificar_estado import VerificarEstadoUseCase
from application.use_cases.enviar_letra import EnviarLetraUseCase, ResultadoJugada

# Etapas del dibujo del ahorcado según las vidas restantes (0 a 6)
DIBUJO_AHORCADO = {
    6: """
       +---+
       |   |
           |
           |
           |
           |
    =========
    """,
    5: """
       +---+
       |   |
       O   |
           |
           |
           |
    =========
    """,
    4: """
       +---+
       |   |
       O   |
       |   |
           |
           |
    =========
    """,
    3: """
       +---+
       |   |
       O   |
      /|   |
           |
           |
    =========
    """,
    2: """
       +---+
       |   |
       O   |
      /|\\  |
           |
           |
    =========
    """,
    1: """
       +---+
       |   |
       O   |
      /|\\  |
      /    |
           |
    =========
    """,
    0: """
       +---+
       |   |
       O   |
      /|\\  |
      / \\  |
           |
    =========
    """
}


class ConsoleUI:
    """
    Capa de Presentación en Consola.
    Solo interactúa con los casos de uso (Clean Architecture).
    Presenta un refresco visual claro del estado global en MongoDB Atlas.
    """

    def __init__(
        self,
        validar_matricula_uc: ValidarMatriculaUseCase,
        verificar_estado_uc: VerificarEstadoUseCase,
        enviar_letra_uc: EnviarLetraUseCase
    ):
        self._validar_matricula_uc = validar_matricula_uc
        self._verificar_estado_uc = verificar_estado_uc
        self._enviar_letra_uc = enviar_letra_uc
        self._alumno: Optional[Alumno] = None
        self._ultimo_mensaje: Optional[str] = None
        self._ultimo_tipo_mensaje: Optional[str] = None

    def limpiar_pantalla(self) -> None:
        """Limpia la terminal según el sistema operativo si se ejecuta interactivamente."""
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")

    def mostrar_encabezado(self) -> None:
        """Muestra el banner principal."""
        print("=" * 65)
        print("     UNIVERSIDAD TECNOLÓGICA METROPOLITANA (UTM) ")
        print("       JUEGO DEL AHORCADO NOSQL - CLIENTE CONCURRENTE")
        print("=" * 65)
        if self._alumno:
            print(f" Alumno autenticado : {self._alumno.nombre_real}")
            print(f" Matrícula          : {self._alumno.matricula}")
            print("-" * 65)

    def login(self) -> Alumno:
        """
        Regla 1: Blindaje de Identidad.
        Pide matrícula al usuario, consulta Atlas y extrae el nombre real
        exclusivamente de la base de datos.
        """
        while True:
            self.limpiar_pantalla()
            self.mostrar_encabezado()
            print("\n[BLINDAJE DE IDENTIDAD]")
            try:
                matricula = input(" Ingrese su matrícula oficial (o 'SALIR'): ").strip()
            except EOFError:
                print("\nEntrada cerrada. Saliendo...")
                sys.exit(0)

            if matricula.upper() in ["SALIR", "EXIT", "Q"]:
                print("\nSaliendo del programa. ¡Hasta pronto!")
                sys.exit(0)

            if not matricula:
                print(" Por favor ingrese una matrícula válida.")
                time.sleep(1.5)
                continue

            print("\n Verificando matrícula en MongoDB Atlas...")
            try:
                alumno = self._validar_matricula_uc.ejecutar(matricula)
                if alumno:
                    print(f" Identidad validada con éxito: {alumno.nombre_real}")
                    time.sleep(1.0)
                    self._alumno = alumno
                    return alumno
                else:
                    print(f" ACCESO DENEGADO: La matrícula '{matricula}' no existe en 'alumnos_registrados'.")
                    try:
                        input(" Presione ENTER para reintentar...")
                    except EOFError:
                        sys.exit(1)
            except ConnectionError as e:
                print(f" Error de conexión con Atlas: {e}")
                try:
                    input(" Presione ENTER para reintentar...")
                except EOFError:
                    sys.exit(1)

    def renderizar_tablero(self, partida: Partida) -> None:
        """Dibuja el tablero del juego en consola."""
        self.limpiar_pantalla()
        self.mostrar_encabezado()

        # Dibujo del ahorcado
        vidas_dibujo = max(0, min(6, partida.vidas_restantes))
        print(DIBUJO_AHORCADO.get(vidas_dibujo, DIBUJO_AHORCADO[0]))

        # Información de la partida
        print(f" PISTA: {partida.pista}\n")

        espacios_str = " ".join(partida.espacios_visibles)
        print(f" PALABRA:  {espacios_str}\n")

        # Representación de vidas
        corazones = "❤️ " * partida.vidas_restantes
        vidas_perdidas = "🖤 " * (6 - partida.vidas_restantes)
        print(f" VIDAS:    [{corazones}{vidas_perdidas}] ({partida.vidas_restantes}/6)")

        letras_str = ", ".join(partida.letras_intentadas) if partida.letras_intentadas else "(ninguna)"
        print(f" LETRAS INTENTADAS: {letras_str}")
        print("-" * 65)

        # Mostrar retroalimentación del último turno
        if self._ultimo_mensaje:
            prefijo = ">>>"
            if self._ultimo_tipo_mensaje in ["VICTORIA", "ACIERTO"]:
                prefijo = " [✓]"
            elif self._ultimo_tipo_mensaje in ["FALLO", "YA_INTENTADA", "CONCURRENCIA_PERDIDA"]:
                prefijo = " [X]"
            print(f"{prefijo} {self._ultimo_mensaje}")
            print("-" * 65)

    def iniciar(self) -> None:
        """
        Bucle continuo del cliente concurrente.
        Refresca el estado global de Atlas, pide jugadas y procesa el resultado.
        """
        # 1. Autenticar identidad
        alumno = self.login()

        # 2. Bucle principal
        while True:
            try:
                # Leer estado actual de 'partida_viva'
                partida = self._verificar_estado_uc.ejecutar("partida_viva")

                if not partida:
                    self.limpiar_pantalla()
                    self.mostrar_encabezado()
                    print("\n[!] No se encontró el documento 'partida_viva' en MongoDB Atlas.")
                    print("     Esperando que el docente inicialice la partida...")
                    opcion = input("\nPresione ENTER para reintentar (o 'SALIR'): ").strip()
                    if opcion.upper() in ["SALIR", "EXIT", "Q"]:
                        break
                    continue

                # Validar si la partida terminó
                if not partida.esta_activa:
                    self.renderizar_tablero(partida)
                    print("\n" + "=" * 65)
                    if partida.es_victoria:
                        print("               🏆 ¡PARTIDA FINALIZADA CON VICTORIA! 🏆")
                        print("=" * 65)
                        print(f" Ganador oficial registrado en Atlas: {partida.ganador}")
                        if alumno.formato_ganador in (partida.ganador or ""):
                            print("\n 🎉 ¡FELICIDADES! TÚ ERES EL GANADOR OFICIAL DE LA PARTIDA 🎉")
                        else:
                            print(f"\n La partida ya fue ganada por otro alumno.")
                    else:
                        print("               💀 ¡VIDAS GLOBALES AGOTADAS! 💀")
                        print("=" * 65)
                        print(f" Resultado oficial: {partida.ganador or 'PERDIDOS (Vidas agotadas)'}")

                    print("=" * 65)
                    print(f" Palabra secreta revelada: '{partida.palabra_secreta}'")
                    print("\n Opciones:")
                    print(" [R] Refrescar estado (por si el docente reinicia la partida)")
                    print(" [Q] Salir del juego")
                    try:
                        opcion = input(" Seleccione una opción: ").strip().upper()
                    except EOFError:
                        break
                    if opcion in ["Q", "SALIR", "EXIT"]:
                        break
                    else:
                        self._ultimo_mensaje = "Estado de partida refrescado."
                        self._ultimo_tipo_mensaje = "INFO"
                        continue

                # Renderizar tablero activo
                self.renderizar_tablero(partida)

                # Pedir letra al usuario
                try:
                    entrada = input("\n Ingrese una letra (o 'SALIR' / 'REFRESCAR'): ").strip().upper()
                except EOFError:
                    break

                if entrada in ["SALIR", "EXIT", "Q"]:
                    print("\nSaliendo del juego...")
                    break

                if entrada in ["REFRESCAR", "R", ""]:
                    self._ultimo_mensaje = "Estado sincronizado con MongoDB Atlas."
                    self._ultimo_tipo_mensaje = "INFO"
                    continue

                if len(entrada) != 1 or not (entrada.isalpha() or entrada == 'Ñ'):
                    self._ultimo_mensaje = "Debe ingresar exactamente una sola letra (A-Z)."
                    self._ultimo_tipo_mensaje = "ERROR_FORMATO"
                    continue

                # Enviar jugada atómica
                print(" Enviando jugada a MongoDB Atlas...")
                resultado: ResultadoJugada = self._enviar_letra_uc.ejecutar(
                    alumno=alumno,
                    letra=entrada,
                    partida_id="partida_viva"
                )

                self._ultimo_mensaje = resultado.mensaje
                self._ultimo_tipo_mensaje = resultado.tipo

                # Si hubo victoria inmediata, dar pequeña pausa de celebración
                if resultado.tipo == "VICTORIA":
                    time.sleep(1.5)

            except ConnectionError as e:
                self._ultimo_mensaje = f"Error de conexión con MongoDB Atlas: {e}"
                self._ultimo_tipo_mensaje = "ERROR"
                time.sleep(2.0)
            except KeyboardInterrupt:
                print("\n\nJuego interrumpido por el usuario. Saliendo...")
                break
            except Exception as e:
                self._ultimo_mensaje = f"Error inesperado: {e}"
                self._ultimo_tipo_mensaje = "ERROR"
                time.sleep(2.0)

        print("\n¡Gracias por jugar! Conexión terminada limpiamente.")
