"""Testes unitários para backend/core/status.py."""
import pytest
from core.status import classificar_transito, status_de_jam, calcular_confianca


# ── helpers ──────────────────────────────────────────────────────────────────

def _s(normal_min: float, transito_min: float) -> str:
    """Chama classificar_transito convertendo minutos para segundos."""
    return classificar_transito(normal_min * 60, transito_min * 60)


# ── classificar_transito ──────────────────────────────────────────────────────

class TestClassificarTransito:
    def test_normal(self):
        # razão ≈ 1.08, atraso = 8min — abaixo de todos os thresholds
        assert _s(100, 108) == "Normal"

    def test_moderado_por_razao(self):
        # razão ≈ 1.20 — acima de THRESHOLDS_RAZAO["Normal"] (1.15)
        assert _s(100, 120) == "Moderado"

    def test_moderado_por_atraso_absoluto(self):
        # atraso 12min, razão ≈ 1.04 — dentro do threshold Moderado (≥10min, >1.03)
        assert _s(300, 312) == "Moderado"

    def test_intenso_por_razao(self):
        # razão ≈ 1.50 — acima de THRESHOLDS_RAZAO["Moderado"] (1.40)
        assert _s(100, 150) == "Intenso"

    def test_intenso_por_atraso_e_razao(self):
        # atraso 30min, razão ≈ 1.06 — dentro do threshold Intenso (≥25min, >1.05)
        assert _s(500, 530) == "Intenso"

    def test_intenso_rota_longa(self):
        # atraso 26min, razão ≈ 1.02 — razão baixa mas atraso > 25 força Intenso
        normal_s = 1300 * 60   # ~21h (rota longa artificial para manter razão baixa)
        transito_s = normal_s + 26 * 60
        assert classificar_transito(normal_s, transito_s) == "Intenso"

    def test_sem_dados(self):
        assert classificar_transito(0, 3600) == "Sem dados"


# ── status_de_jam ─────────────────────────────────────────────────────────────

class TestStatusDeJam:
    def test_normal(self):
        assert status_de_jam(2, 2) == "Normal"

    def test_moderado_por_jam_max(self):
        assert status_de_jam(6, 2) == "Moderado"

    def test_moderado_por_jam_avg(self):
        assert status_de_jam(3, 5) == "Moderado"

    def test_intenso(self):
        assert status_de_jam(8, 3) == "Intenso"

    def test_intenso_fronteira(self):
        assert status_de_jam(9, 3) == "Intenso"

    def test_parado_por_jam_max(self):
        assert status_de_jam(10, 5) == "Parado"

    def test_parado_por_road_closed(self):
        assert status_de_jam(2, 2, road_closed=True) == "Parado"


# ── calcular_confianca ────────────────────────────────────────────────────────

class TestCalcularConfianca:
    def test_alta(self):
        assert calcular_confianca(True, True, 0) == ("Alta", 100)

    def test_media_google(self):
        assert calcular_confianca(True, False, 0) == ("Média", 50)

    def test_media_here(self):
        assert calcular_confianca(False, True, 0) == ("Média", 50)

    def test_baixa(self):
        assert calcular_confianca(False, False, 0) == ("Baixa", 0)
