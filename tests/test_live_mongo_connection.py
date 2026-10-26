"""Prueba de integración con el clúster en vivo de MongoDB Atlas."""
import unittest
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

from infrastructure.database.mongo_client import MongoDBConnection
from infrastructure.repositories.mongo_game_repository import MongoGameRepository


class TestLiveMongoIntegration(unittest.TestCase):
    def setUp(self):
        self.db_conn = MongoDBConnection()
        self.repo = MongoGameRepository(self.db_conn)

    def tearDown(self):
        self.db_conn.close()

    def test_live_connection_and_reading_partida(self):
        partida = self.repo.obtener_partida_viva("partida_viva")
        self.assertIsNotNone(partida, "El documento 'partida_viva' debe existir en Atlas")
        self.assertEqual(partida.id, "partida_viva")
        self.assertTrue(len(partida.palabra_secreta) > 0)
        self.assertTrue(isinstance(partida.vidas_restantes, int))

    def test_live_lookup_alumno_invalido(self):
        alumno = self.repo.buscar_alumno_por_matricula("000000000")
        self.assertIsNone(alumno, "Una matrícula inválida debe retornar None")

    def test_live_lookup_alumno_valido(self):
        # Matrícula conocida de un alumno registrado
        alumno = self.repo.buscar_alumno_por_matricula("24090592")
        self.assertIsNotNone(alumno, "La matrícula '24090592' debe existir")
        self.assertEqual(alumno.matricula, "24090592")
        self.assertEqual(alumno.nombre_real, "ANDRADE HOMA")


if __name__ == "__main__":
    unittest.main()
