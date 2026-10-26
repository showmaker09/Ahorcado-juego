#!/usr/bin/env python3
"""
Actividad 8 – Ahorcado NoSQL Concurrente
Universidad Tecnológica Metropolitana (UTM)

Punto de entrada principal (Composition Root).
Ensambla dependencias siguiendo Clean Architecture:
  Infrastructure -> Repository -> Use Cases -> Presentation
"""

import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Cargar variables de entorno desde el archivo .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Configurar logging básico
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARNING),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AhorcadoNoSQL")

from infrastructure.database.mongo_client import MongoDBConnection
from infrastructure.repositories.mongo_game_repository import MongoGameRepository
from application.use_cases.validar_matricula import ValidarMatriculaUseCase
from application.use_cases.verificar_estado import VerificarEstadoUseCase
from application.use_cases.enviar_letra import EnviarLetraUseCase
from presentation.console_ui import ConsoleUI


def main() -> None:
    db_conn = None
    try:
        # 1. Capa de Infraestructura (Base de datos y Repositorio)
        db_conn = MongoDBConnection()
        repository = MongoGameRepository(db_connection=db_conn)

        # 2. Capa de Aplicación (Casos de uso con Inyección de Dependencias)
        validar_matricula_uc = ValidarMatriculaUseCase(repository=repository)
        verificar_estado_uc = VerificarEstadoUseCase(repository=repository)
        enviar_letra_uc = EnviarLetraUseCase(repository=repository)

        # 3. Capa de Presentación (UI de Consola)
        ui = ConsoleUI(
            validar_matricula_uc=validar_matricula_uc,
            verificar_estado_uc=verificar_estado_uc,
            enviar_letra_uc=enviar_letra_uc
        )

        # 4. Iniciar ejecución del cliente interactivo
        ui.iniciar()

    except ConnectionError as e:
        print(f"\n[ERROR CRÍTICO DE CONEXIÓN] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nPrograma finalizado por el usuario.")
    except Exception as e:
        logger.critical(f"Excepción no controlada en la aplicación: {e}", exc_info=True)
        print(f"\n[ERROR INESPERADO] {e}")
        sys.exit(1)
    finally:
        if db_conn:
            db_conn.close()


if __name__ == "__main__":
    main()
