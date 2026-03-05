"""Testes unitários para backend/core/status.py."""
import pytest
from core.status import (
    classificar_transito,
    status_de_jam,
    calcular_confianca,
    aplicar_override_ocorrencia,
    inferir_ocorrencia,
)


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


# ── aplicar_override_ocorrencia ───────────────────────────────────────────────

class TestAplicarOverrideOcorrencia:
    def test_interdicao_eleva_para_parado(self):
        assert aplicar_override_ocorrencia("Normal", "Interdição") == "Parado"

    def test_interdicao_mantem_parado(self):
        assert aplicar_override_ocorrencia("Parado", "Interdição") == "Parado"

    def test_colisao_eleva_para_intenso(self):
        assert aplicar_override_ocorrencia("Normal", "Colisão") == "Intenso"

    def test_colisao_nao_rebaixa_parado(self):
        assert aplicar_override_ocorrencia("Parado", "Colisão") == "Parado"

    def test_acidente_eleva_para_intenso(self):
        assert aplicar_override_ocorrencia("Moderado", "Acidente") == "Intenso"

    def test_bloqueio_parcial_eleva_para_moderado(self):
        assert aplicar_override_ocorrencia("Normal", "Bloqueio Parcial") == "Moderado"

    def test_bloqueio_parcial_nao_rebaixa_intenso(self):
        assert aplicar_override_ocorrencia("Intenso", "Bloqueio Parcial") == "Intenso"

    def test_engarrafamento_sem_override(self):
        assert aplicar_override_ocorrencia("Moderado", "Engarrafamento") == "Moderado"

    def test_sem_ocorrencia(self):
        assert aplicar_override_ocorrencia("Normal", "") == "Normal"


# ── inferir_ocorrencia ────────────────────────────────────────────────────────

class TestInferirOcorrencia:
    def test_usa_categoria_do_incidente(self):
        inc = {"categoria": "Colisão", "descricao": "Acidente na pista"}
        assert inferir_ocorrencia(inc, jam_max=0, atraso_min=0) == "Colisão"

    def test_infere_engarrafamento_por_jam(self):
        assert inferir_ocorrencia(None, jam_max=6, atraso_min=0) == "Engarrafamento"

    def test_infere_engarrafamento_por_atraso(self):
        assert inferir_ocorrencia(None, jam_max=0, atraso_min=15) == "Engarrafamento"

    def test_sem_ocorrencia_quando_tudo_normal(self):
        assert inferir_ocorrencia(None, jam_max=2, atraso_min=5) == ""

    def test_incidente_tem_prioridade_sobre_jam(self):
        inc = {"categoria": "Obras na Pista"}
        assert inferir_ocorrencia(inc, jam_max=8, atraso_min=20) == "Obras na Pista"
