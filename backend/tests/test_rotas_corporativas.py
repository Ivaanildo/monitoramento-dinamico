import pytest
from core.rotas_corporativas import (
    carregar_rotas,
    buscar_rota_por_id,
    converter_para_parametros_consulta,
)

# Mocked config. It should point to the real default or rely on fallback if not found.
# In a real environment we might mock the file loading for pure unit tests,
# but the prompt asks to validate loading the 20 routes from the actual file.
_mock_config = {}

def test_carregar_20_rotas():
    rotas = carregar_rotas(_mock_config)
    assert len(rotas) == 20, f"Deveria carregar 20 rotas, carregou {len(rotas)}"
    
    # Valida estrutura de uma rota qualquer
    rota = rotas[0]
    assert "id" in rota
    assert "origem" in rota
    assert "destino" in rota
    assert "via" in rota
    assert "rodovia_logica" in rota

def test_buscar_rota_por_id_existente():
    rota = buscar_rota_por_id(_mock_config, "R01")
    assert rota is not None
    assert rota["id"] == "R01"

def test_buscar_rota_por_id_inexistente():
    rota = buscar_rota_por_id(_mock_config, "R99")
    assert rota is None

def test_converter_para_parametros():
    rota = {
        "id": "R01",
        "origem": "-23,-46",
        "destino": "-8,-35",
        "via": ["passThrough=true"],
        "rodovia_logica": ["BR-116"],
    }
    params = converter_para_parametros_consulta(rota)
    assert params["origem"] == "-23,-46"
    assert params["destino"] == "-8,-35"
    assert params["via"] == ["passThrough=true"]
    assert params["rodovia_logica"] == ["BR-116"]
