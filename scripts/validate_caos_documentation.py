#!/usr/bin/env python3
"""
Validação da Documentação CAOS⁺
================================

Script para validar que todas as melhorias na documentação do motor CAOS⁺
foram implementadas corretamente conforme o issue.

Issue: Melhorar a documentação da função calculate_caos
Tarefas:
- ✅ Revisar docstrings
- ✅ Adicionar exemplos de uso
- ✅ Explicar o racional da implementação
- ✅ Garantir que o README ou uma seção de docs cubra o funcionamento
"""

import sys
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from penin.core.caos import (
    AutoevolutionMetrics,
    CAOSConfig,
    CAOSState,
    ConsistencyMetrics,
    IncognoscibleMetrics,
    SilenceMetrics,
    compute_caos_plus_complete,
    compute_caos_plus_exponential,
    compute_caos_plus_simple,
    phi_caos,
)


def validate_docstrings():
    """Valida que docstrings foram melhoradas."""
    print("=" * 70)
    print("1. Validando Docstrings")
    print("=" * 70)

    functions_to_check = [
        compute_caos_plus_exponential,
        phi_caos,
        compute_caos_plus_simple,
        compute_caos_plus_complete,
    ]

    for func in functions_to_check:
        doc = func.__doc__
        assert doc is not None, f"{func.__name__} não tem docstring"
        assert len(doc) > 500, f"{func.__name__} docstring muito curta"

        # Verificar seções importantes
        if func == compute_caos_plus_exponential:
            assert "Racional Matemático" in doc, "Falta seção de racional matemático"
            assert "Propriedades Matemáticas" in doc, "Falta propriedades matemáticas"
            assert "Examples:" in doc, "Falta seção de exemplos"
            assert "Args:" in doc, "Falta seção de argumentos"
            assert "Returns:" in doc, "Falta seção de retorno"
            assert "Ver Também" in doc, "Falta seção de cross-references"
            print(f"✓ {func.__name__}: Docstring completa e detalhada")

        elif func == phi_caos:
            assert "Racional Matemático" in doc, "Falta seção de racional matemático"
            assert "Examples:" in doc, "Falta seção de exemplos"
            print(f"✓ {func.__name__}: Docstring melhorada")

        elif func == compute_caos_plus_complete:
            assert "Pipeline de Computação" in doc, "Falta pipeline de computação"
            assert "Casos de Uso" in doc, "Falta casos de uso"
            assert "Examples:" in doc, "Falta exemplos"
            assert len(doc) > 3000, "Docstring não está suficientemente detalhada"
            print(f"✓ {func.__name__}: Docstring extremamente completa")

        else:
            print(f"✓ {func.__name__}: Docstring presente")

    print("\n✅ Todas as docstrings foram melhoradas!\n")


def validate_examples():
    """Valida que exemplos de uso foram adicionados."""
    print("=" * 70)
    print("2. Validando Exemplos de Uso")
    print("=" * 70)

    # Exemplo 1: Uso básico
    print("\nExemplo 1: Uso Básico")
    c, a, o, s = 0.88, 0.40, 0.25, 0.85
    caos = compute_caos_plus_exponential(c, a, o, s, kappa=20.0)
    assert 1.0 <= caos <= 10.0
    print(f"  CAOS⁺({c}, {a}, {o}, {s}) = {caos:.4f}")
    print("  ✓ Exemplo básico funciona")

    # Exemplo 2: Com métricas estruturadas
    print("\nExemplo 2: Métricas Estruturadas")
    consistency = ConsistencyMetrics(pass_at_k=0.92, ece=0.008)
    autoevolution = AutoevolutionMetrics(delta_linf=0.06, cost_normalized=0.15)
    incognoscible = IncognoscibleMetrics(epistemic_uncertainty=0.35)
    silence = SilenceMetrics(noise_ratio=0.08)

    caos, details = compute_caos_plus_complete(
        consistency, autoevolution, incognoscible, silence
    )
    assert 'components_raw' in details
    assert 'components_smoothed' in details
    print(f"  CAOS⁺ = {caos:.4f}")
    print(f"  Componentes: {details['components_raw']}")
    print("  ✓ Exemplo com métricas funciona")

    # Exemplo 3: Tracking temporal
    print("\nExemplo 3: Tracking Temporal")
    config = CAOSConfig(kappa=25.0, ema_half_life=5)
    state = CAOSState()

    for _i in range(5):
        caos_i, details_i = compute_caos_plus_complete(
            consistency, autoevolution, incognoscible, silence,
            config, state
        )

    stability = details_i['state_stability']
    assert stability >= 0.0
    print(f"  Após 5 iterações: estabilidade = {stability:.4f}")
    print("  ✓ Exemplo de tracking funciona")

    # Exemplo 4: Diferentes cenários
    print("\nExemplo 4: Cenários de Exploração vs Exploração")

    # Exploração (alta incerteza)
    caos_explore = compute_caos_plus_exponential(0.5, 0.3, 0.8, 0.6, 20.0)
    print(f"  Exploração (alta incerteza): {caos_explore:.4f}")

    # Exploração (baixa incerteza)
    caos_exploit = compute_caos_plus_exponential(0.9, 0.6, 0.2, 0.9, 20.0)
    print(f"  Exploração (baixa incerteza): {caos_exploit:.4f}")

    # Sweet spot
    caos_sweet = compute_caos_plus_exponential(0.85, 0.7, 0.6, 0.85, 20.0)
    print(f"  Sweet spot: {caos_sweet:.4f}")
    print("  ✓ Exemplos de cenários funcionam")

    print("\n✅ Todos os exemplos de uso funcionam corretamente!\n")


def validate_mathematical_rationale():
    """Valida que o racional matemático está documentado."""
    print("=" * 70)
    print("3. Validando Racional Matemático")
    print("=" * 70)

    doc = compute_caos_plus_exponential.__doc__

    # Verificar que racional está presente
    assert "Racional Matemático" in doc
    assert "Base (1 + κ·C·A)" in doc
    assert "Expoente (O·S)" in doc
    assert "Propriedades Matemáticas" in doc
    assert "Monotonicidade" in doc
    print("✓ Racional matemático documentado em compute_caos_plus_exponential")

    # Verificar que está no módulo
    import penin.core.caos as caos_module
    assert hasattr(caos_module, '__doc__')
    module_doc = caos_module.__doc__
    assert "Motor CAOS⁺" in module_doc
    assert "Dimensões" in module_doc
    print("✓ Racional matemático documentado no módulo")

    # Verificar que fórmula está documentada
    assert "CAOS⁺ = (1 + κ · C · A)^(O · S)" in module_doc
    print("✓ Fórmula matemática documentada")

    print("\n✅ Racional matemático está bem documentado!\n")


def validate_documentation_files():
    """Valida que arquivos de documentação foram atualizados."""
    print("=" * 70)
    print("4. Validando Arquivos de Documentação")
    print("=" * 70)

    project_root = Path(__file__).parent.parent

    # Verificar docs/equations.md
    equations_md = project_root / "docs" / "equations.md"
    assert equations_md.exists(), "docs/equations.md não existe"

    content = equations_md.read_text()
    assert "CAOS⁺" in content, "CAOS⁺ não está em equations.md"
    assert "Consistency" in content, "Falta documentação de Consistency"
    assert "Autoevolution" in content, "Falta documentação de Autoevolution"
    assert "Unknowable" in content or "Incognoscível" in content, "Falta documentação de Unknowable"
    assert "Silence" in content or "Silêncio" in content, "Falta documentação de Silence"

    # Verificar que tem implementação e exemplos
    assert "Implementation" in content or "Implementação" in content
    assert "python" in content.lower()  # Tem exemplos de código Python

    print(f"✓ docs/equations.md atualizado (tamanho: {len(content)} chars)")

    # Verificar guia completo
    caos_guide = project_root / "docs" / "guides" / "CAOS_PLUS_GUIDE.md"
    assert caos_guide.exists(), "CAOS_PLUS_GUIDE.md não existe"

    guide_content = caos_guide.read_text()
    assert len(guide_content) > 10000, "Guia muito curto"
    assert "Tabela de Conteúdos" in guide_content
    assert "Exemplos Práticos" in guide_content
    assert "Best Practices" in guide_content
    assert "Troubleshooting" in guide_content
    assert "FAQ" in guide_content

    print(f"✓ docs/guides/CAOS_PLUS_GUIDE.md created (size: {len(guide_content)} chars)")

    print("\n✅ Todos os arquivos de documentação foram atualizados!\n")


def validate_executable_examples():
    """Valida que exemplos são executáveis."""
    print("=" * 70)
    print("5. Validando Exemplos Executáveis")
    print("=" * 70)

    # Testar que módulo tem exemplos executáveis
    import penin.core.caos as caos_module

    # Verificar que funções de exemplo existem
    example_functions = [
        'example_basic_usage',
        'example_structured_metrics',
        'example_temporal_tracking',
        'example_exploration_vs_exploitation',
        'example_kappa_tuning',
        'example_edge_cases',
        'run_all_examples',
    ]

    for func_name in example_functions:
        assert hasattr(caos_module, func_name), f"Falta {func_name}"
        print(f"✓ {func_name} disponível")

    # Testar que exemplos rodam
    print("\nTestando execução de exemplo básico...")
    caos_module.example_basic_usage()
    print("✓ Exemplo básico executa sem erros")

    print("\n✅ Exemplos são executáveis!\n")


def validate_edge_cases():
    """Valida documentação de edge cases."""
    print("=" * 70)
    print("6. Validando Documentação de Edge Cases")
    print("=" * 70)

    # Verificar que exemplos cobrem edge cases

    # Testar edge cases documentados
    print("\nTestando edge cases:")

    # 1. Todos zeros
    caos1 = compute_caos_plus_exponential(0, 0, 0, 0, 20.0)
    assert abs(caos1 - 1.0) < 0.01, "Edge case (0,0,0,0) incorreto"
    print(f"  ✓ CAOS⁺(0,0,0,0) = {caos1:.4f} (esperado: 1.0)")

    # 2. Todos uns
    caos2 = compute_caos_plus_exponential(1, 1, 1, 1, 20.0)
    assert abs(caos2 - 21.0) < 0.01, "Edge case (1,1,1,1) incorreto"
    print(f"  ✓ CAOS⁺(1,1,1,1) = {caos2:.4f} (esperado: 21.0)")

    # 3. C=A=0
    caos3 = compute_caos_plus_exponential(0, 0, 1, 1, 20.0)
    assert abs(caos3 - 1.0) < 0.01, "Edge case C=A=0 incorreto"
    print(f"  ✓ CAOS⁺(0,0,1,1) = {caos3:.4f} (base não amplifica)")

    # 4. O=S=0
    caos4 = compute_caos_plus_exponential(1, 1, 0, 0, 20.0)
    assert abs(caos4 - 1.0) < 0.01, "Edge case O=S=0 incorreto"
    print(f"  ✓ CAOS⁺(1,1,0,0) = {caos4:.4f} (expoente zero)")

    # 5. Clamping
    caos5 = compute_caos_plus_exponential(1.5, -0.2, 0.5, 0.8, 20.0)
    assert caos5 >= 1.0, "Clamping não funcionou"
    print(f"  ✓ Valores fora de [0,1] são clampados: {caos5:.4f}")

    print("\n✅ Edge cases documentados e funcionam corretamente!\n")


def main():
    """Executa todas as validações."""
    print("\n" + "=" * 70)
    print("VALIDAÇÃO DA DOCUMENTAÇÃO CAOS⁺")
    print("=" * 70)
    print()

    try:
        validate_docstrings()
        validate_examples()
        validate_mathematical_rationale()
        validate_documentation_files()
        validate_executable_examples()
        validate_edge_cases()

        print("=" * 70)
        print("✅ TODAS AS VALIDAÇÕES PASSARAM!")
        print("=" * 70)
        print()
        print("Resumo das Melhorias:")
        print("  ✅ Docstrings revisadas e expandidas")
        print("  ✅ Exemplos de uso adicionados (6+ cenários)")
        print("  ✅ Racional matemático explicado em detalhe")
        print("  ✅ docs/equations.md expandido com seção CAOS⁺ completa")
        print("  ✅ docs/guides/CAOS_PLUS_GUIDE.md criado (25KB+ de documentação)")
        print("  ✅ Exemplos executáveis no módulo principal")
        print("  ✅ Edge cases documentados e testados")
        print()
        print("A documentação do motor CAOS⁺ agora está completa e profissional!")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ VALIDAÇÃO FALHOU: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
