"""Testes unitários para backend/core/status.py."""
import pytest
from core.status import (
    classificar_transito,
    status_de_jam,
    calcular_confianca,
    aplicar_override_ocorrencia,
    inferir_ocorrencia,
    gerar_observacao,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _s(normal_min: float, transito_min: float) -> str:
    """Chama classificar_transito convertendo minutos para segundos."""
    return classificar_transito(normal_min * 60, transito_min * 60)


# ── classificar_transito ──────────────────────────────────────────────────────

class TestClassificarTransito:
    def test_normal_sem_atraso(self):
        assert _s(100, 108) == "Normal"

    def test_normal_atraso_5min_razao_alta(self):
        # atraso 5 min, razão 1.20 — abaixo de 20 min → Normal
        assert _s(25, 30) == "Normal"

    def test_normal_atraso_17min(self):
        # atraso 17 min — abaixo de 20 min → Normal
        assert _s(100, 117) == "Normal"

    def test_normal_atraso_20min_exato(self):
        # atraso exatamente 20 min — não é > 20 → Normal
        assert _s(100, 120) == "Normal"

    def test_moderado_atraso_21min(self):
        # atraso 21 min — > 20 → Moderado
        assert _s(100, 121) == "Moderado"

    def test_moderado_atraso_29min(self):
        assert _s(100, 129) == "Moderado"

    def test_intenso_atraso_30min(self):
        # atraso 30 min — >= 30 → Intenso
        assert _s(100, 130) == "Intenso"

    def test_intenso_atraso_35min(self):
        assert _s(100, 135) == "Intenso"

    def test_intenso_rota_longa(self):
        # atraso 35 min em rota longa
        normal_s = 1300 * 60
        transito_s = normal_s + 35 * 60
        assert classificar_transito(normal_s, transito_s) == "Intenso"

    def test_sem_dados(self):
        assert classificar_transito(0, 3600) == "Sem dados"


# ── status_de_jam ─────────────────────────────────────────────────────────────

class TestStatusDeJam:
    def test_normal(self):
        assert status_de_jam(2, 2) == "Normal"

    def test_normal_jam_alto_sem_pct_cong(self):
        # jam_max=6, pct_cong=5 — sem guard pct_cong >= 10 → Normal
        assert status_de_jam(6, 2, pct_cong=5) == "Normal"

    def test_moderado_com_pct_cong(self):
        # jam_max=6, pct_cong=12 — >= 10 → Moderado
        assert status_de_jam(6, 2, pct_cong=12) == "Moderado"

    def test_moderado_por_jam_avg_com_pct(self):
        assert status_de_jam(3, 5, pct_cong=10) == "Moderado"

    def test_intenso(self):
        assert status_de_jam(8, 3, pct_cong=15) == "Intenso"

    def test_intenso_fronteira(self):
        assert status_de_jam(9, 3, pct_cong=20) == "Intenso"

    def test_intenso_sem_pct_cong_suficiente(self):
        # jam_max=8, pct_cong=10 — não atinge pct >= 15 para Intenso,
        # mas atinge pct >= 10 para Moderado
        assert status_de_jam(8, 3, pct_cong=10) == "Moderado"

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
        assert inferir_ocorrencia(None, jam_max=0, atraso_min=20) == "Engarrafamento"

    def test_sem_ocorrencia_quando_tudo_normal(self):
        assert inferir_ocorrencia(None, jam_max=2, atraso_min=5) == ""

    def test_incidente_tem_prioridade_sobre_jam(self):
        inc = {"categoria": "Obras na Pista"}
        assert inferir_ocorrencia(inc, jam_max=8, atraso_min=20) == "Obras na Pista"


# ── gerar_observacao ──────────────────────────────────────────────────────────

class TestGerarObservacao:
    def test_com_incidente_e_atraso(self):
        inc = {"categoria": "Colisão", "descricao": "Batida"}
        obs = gerar_observacao(
            inc=inc, atraso_min=25, dur_normal=100, dur_transito=125,
            pct_cong=20, jam_avg=6, vel_atual=40, vel_livre=80,
            sigla="BR-116", hub_origem="SP", hub_destino="RJ",
        )
        assert "Colisão (Google Maps) em BR-116" in obs
        assert "Atraso 25 min" in obs

    def test_sem_incidente_com_atraso(self):
        obs = gerar_observacao(
            inc=None, atraso_min=10, dur_normal=60, dur_transito=70,
            pct_cong=5, jam_avg=3, vel_atual=50, vel_livre=80,
            sigla="BR-381",
        )
        assert "Engarrafamento (Google Maps) em BR-381" in obs
        assert "Atraso 10 min" in obs

    def test_fluxo_livre_com_hubs(self):
        obs = gerar_observacao(
            inc=None, atraso_min=0, dur_normal=60, dur_transito=60,
            pct_cong=0, jam_avg=1, vel_atual=80, vel_livre=80,
            sigla="BR-116", hub_origem="SP", hub_destino="RJ",
        )
        assert obs == "Via BR-116, sentido SP -> RJ sem anormalidades, fluxo livre."

    def test_incidente_sem_atraso(self):
        inc = {"categoria": "Obras na Pista", "descricao": "Manutencao noturna", "rodovia_afetada": "BR-116"}
        obs = gerar_observacao(
            inc=inc, atraso_min=0, dur_normal=60, dur_transito=60,
            pct_cong=0, jam_avg=1, vel_atual=80, vel_livre=80,
            sigla="BR-116", hub_origem="SP", hub_destino="RJ",
        )
        assert "Obras na Pista em BR-116" in obs
        assert "Sem impacto no tempo de viagem" in obs
        assert "Manutencao noturna" in obs

    def test_fluxo_livre_sem_hubs(self):
        obs = gerar_observacao(
            inc=None, atraso_min=0, dur_normal=60, dur_transito=60,
            pct_cong=0, jam_avg=1, vel_atual=80, vel_livre=80,
        )
        assert obs == "Via trecho monitorado sem anormalidades, fluxo livre."
