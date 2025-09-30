#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω CLI - Command Line Interface
===================================

Comandos principais:
- penin evolve --n 6 --budget "30m" --provider <id> --dry-run
- penin evaluate --model path|provider --suite basic
- penin promote --run <id>
- penin rollback --to <id|LAST_GOOD>
- penin dashboard --serve
- penin status --verbose

Interface unificada para operação do sistema PENIN-Ω.
"""

import sys
import argparse
import json
import time
from pathlib import Path

# Imports dos módulos Omega
try:
    from penin.omega.runners import EvolutionRunner, CycleConfig, BatchRunner
    from penin.omega.evaluators import ComprehensiveEvaluator
    from penin.omega.ledger import WORMLedger
    from penin.omega.mutators import ChallengerGenerator
    from penin.omega.tuner import PeninAutoTuner
    from observability import ObservabilityManager, ObservabilityConfig
except ImportError:
    # Fallback para desenvolvimento
    import sys
    sys.path.append('/workspace')
    try:
        from penin.omega.runners import EvolutionRunner, CycleConfig, BatchRunner
        from penin.omega.evaluators import ComprehensiveEvaluator
        from penin.omega.ledger import WORMLedger
        from penin.omega.mutators import ChallengerGenerator
        from penin.omega.tuner import PeninAutoTuner
        from observability import ObservabilityManager, ObservabilityConfig
    except ImportError as e2:
        print(f"❌ Erro ao importar módulos PENIN: {e2}")
        print("   Certifique-se de que todos os módulos estão no PYTHONPATH")
        sys.exit(1)


class PeninCLI:
    """Interface CLI principal"""

    def __init__(self):
        self.data_dir = Path.home() / ".penin_omega"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Componentes principais
        self.ledger = WORMLedger(
            db_path=self.data_dir / "cli_ledger.db",
            runs_dir=self.data_dir / "cli_runs"
        )

        self.runner = EvolutionRunner(
            ledger_path=self.data_dir / "evolution_ledger.db",
            runs_dir=self.data_dir / "evolution_runs"
        )

    def cmd_evolve(self, args) -> int:
        """Comando: penin evolve"""
        print("🚀 PENIN Evolve - Ciclo de Auto-Evolução")
        print("=" * 50)

        # Configuração do ciclo
        config = CycleConfig(
            n_challengers=args.n_challengers,
            budget_usd=args.budget,
            provider_id=args.provider,
            dry_run=args.dry_run,
            enable_tuning=not args.no_tuning,
            enable_canary=not args.no_canary
        )

        print("Configuração:")
        print(f"  Challengers: {config.n_challengers}")
        print(f"  Budget: ${config.budget_usd:.2f}")
        print(f"  Provider: {config.provider_id}")
        print(f"  Dry run: {config.dry_run}")
        print(f"  Tuning: {config.enable_tuning}")
        print(f"  Canary: {config.enable_canary}")
        print()

        # Modelo mock (em produção seria provider real)
        def mock_model(prompt: str) -> str:
            if "json" in prompt.lower():
                return '{"extracted": "data"}'
            elif "resumo" in prompt.lower():
                return "Resumo gerado automaticamente"
            else:
                return f"Resposta para: {prompt[:50]}..."

        try:
            # Executar ciclo
            if args.batch and args.batch > 1:
                # Batch de ciclos
                batch_runner = BatchRunner(self.runner)
                result = batch_runner.run_batch(args.batch, config, mock_model)

                print("\n✅ Batch completo:")
                print(f"   Ciclos: {result['total_cycles']}")
                print(f"   Sucessos: {result['successful_cycles']}")
                print(f"   Taxa: {result['success_rate']*100:.1f}%")

                return 0 if result['successful_cycles'] > 0 else 1
            else:
                # Ciclo único
                result = self.runner.evolve_one_cycle(config, mock_model)

                print(f"\n✅ Ciclo {result.cycle_id[:8]}... completo:")
                print(f"   Sucesso: {result.success}")
                print(f"   Duração: {result.duration_s:.2f}s")
                print(f"   Promoções: {result.promotions}")

                return 0 if result.success else 1

        except Exception as e:
            print(f"❌ Erro na evolução: {e}")
            return 1

    def cmd_evaluate(self, args) -> int:
        """Comando: penin evaluate"""
        print("📊 PENIN Evaluate - Avaliação de Modelo")
        print("=" * 50)

        print(f"Modelo: {args.model}")
        print(f"Suíte: {args.suite}")
        print()

        # Modelo mock
        def mock_model(prompt: str) -> str:
            return f"Avaliação de: {prompt[:30]}..."

        try:
            # Executar avaliação
            evaluator = ComprehensiveEvaluator()

            result = evaluator.evaluate_model(
                mock_model,
                config={"model": args.model, "suite": args.suite},
                provider_id=args.model,
                model_name=args.model
            )

            print("✅ Avaliação completa:")
            print(f"   U (Utilidade): {result.U:.3f}")
            print(f"   S (Estabilidade): {result.S:.3f}")
            print(f"   C (Custo): {result.C:.3f}")
            print(f"   L (Aprendizado): {result.L:.3f}")
            print()
            print(f"   Tokens: {result.total_tokens}")
            print(f"   Custo: ${result.total_cost_usd:.4f}")
            print(f"   Latência: {result.avg_latency_ms:.1f}ms")

            # Salvar resultado
            if args.save:
                output_file = self.data_dir / f"evaluation_{int(time.time())}.json"
                with open(output_file, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2)
                print(f"   💾 Salvo em: {output_file}")

            return 0

        except Exception as e:
            print(f"❌ Erro na avaliação: {e}")
            return 1

    def cmd_promote(self, args) -> int:
        """Comando: penin promote"""
        print("🚀 PENIN Promote - Promoção Manual")
        print("=" * 50)

        run_id = args.run_id
        print(f"Promovendo run: {run_id}")

        try:
            # Verificar se run existe
            record = self.ledger.get_record(run_id)
            if not record:
                print(f"❌ Run {run_id} não encontrado")
                return 1

            # Promover
            success = self.ledger.set_champion(run_id)

            if success:
                print(f"✅ {run_id[:8]}... promovido para champion")

                # Mostrar métricas
                print(f"   U: {record.metrics.U:.3f}")
                print(f"   S: {record.metrics.S:.3f}")
                print(f"   C: {record.metrics.C:.3f}")
                print(f"   L: {record.metrics.L:.3f}")

                return 0
            else:
                print(f"❌ Falha na promoção de {run_id}")
                return 1

        except Exception as e:
            print(f"❌ Erro na promoção: {e}")
            return 1

    def cmd_rollback(self, args) -> int:
        """Comando: penin rollback"""
        print("⏪ PENIN Rollback - Reverter Champion")
        print("=" * 50)

        target = args.target
        print(f"Rollback para: {target}")

        try:
            if target == "LAST_GOOD":
                # Rollback para último champion
                champion = self.ledger.get_champion()
                if not champion:
                    print("❌ Nenhum champion encontrado")
                    return 1
                target_id = champion.run_id
            else:
                target_id = target

            # Executar rollback
            success = self.runner.rollback_to_cycle(target_id)

            if success:
                print(f"✅ Rollback para {target_id[:8]}... completo")
                return 0
            else:
                print(f"❌ Falha no rollback para {target_id}")
                return 1

        except Exception as e:
            print(f"❌ Erro no rollback: {e}")
            return 1

    def cmd_status(self, args) -> int:
        """Comando: penin status"""
        print("📊 PENIN Status - Estado do Sistema")
        print("=" * 50)

        try:
            # Status do runner
            runner_status = self.runner.get_runner_status()

            print("🔄 Evolution Runner:")
            print(f"   Ciclos executados: {runner_status['cycle_count']}")
            print(f"   Histórico de avaliações: {runner_status['evaluation_history_size']}")

            # Status da liga
            league_status = runner_status.get("league_status", {})
            champion_info = league_status.get("champion", {})

            print("\n🏆 Liga:")
            if champion_info.get("run_id"):
                print(f"   Champion: {champion_info['run_id'][:8]}...")
                if champion_info.get("timestamp"):
                    champion_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                                 time.localtime(champion_info["timestamp"]))
                    print(f"   Desde: {champion_time}")
            else:
                print("   Champion: Nenhum")

            print(f"   Challengers ativos: {league_status.get('active_challengers', 0)}")
            print(f"   Canários ativos: {league_status.get('active_canaries', 0)}")

            # Status do ledger
            ledger_stats = runner_status.get("ledger_stats", {})
            print("\n📝 Ledger:")
            print(f"   Total records: {ledger_stats.get('total_records', 0)}")
            print(f"   Decisões: {ledger_stats.get('decisions', {})}")
            print(f"   WAL habilitado: {ledger_stats.get('wal_enabled', False)}")

            # Status do tuning (se verbose)
            if args.verbose:
                tuning_stats = runner_status.get("tuning_stats", {})
                if tuning_stats:
                    print("\n🎛️  Auto-Tuning:")
                    state = tuning_stats.get("state", {})
                    print(f"   Ciclos: {state.get('cycle', 0)}")
                    print(f"   Updates: {state.get('total_updates', 0)}")
                    print(f"   Melhor objetivo: {state.get('best_objective', 0):.4f}")
                    print(f"   Convergiu: {state.get('converged', False)}")

                    # Parâmetros atuais
                    params = tuning_stats.get("parameters", {})
                    if params:
                        print("   Parâmetros:")
                        for name, param_info in params.items():
                            value = param_info.get("current_value", 0)
                            print(f"     {name}: {value:.4f}")

            return 0

        except Exception as e:
            print(f"❌ Erro ao obter status: {e}")
            return 1

    def cmd_dashboard(self, args) -> int:
        """Comando: penin dashboard"""
        print("📊 PENIN Dashboard - Observabilidade")
        print("=" * 50)

        if args.serve:
            print("🌐 Iniciando servidor de observabilidade...")

            try:
                # Configurar observabilidade
                obs_config = ObservabilityConfig(
                    enable_metrics=True,
                    metrics_port=args.port,
                    metrics_auth_token=args.auth_token,
                    enable_json_logs=True
                )

                obs = ObservabilityManager(obs_config)
                obs.start()

                print("✅ Dashboard disponível:")
                print(f"   Métricas: http://127.0.0.1:{args.port}/metrics")
                print(f"   Health: http://127.0.0.1:{args.port}/health")

                if args.auth_token:
                    print(f"   Auth: Bearer {args.auth_token}")

                print("\n🔄 Pressione Ctrl+C para parar...")

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Parando dashboard...")
                    obs.stop()

                return 0

            except Exception as e:
                print(f"❌ Erro no dashboard: {e}")
                return 1
        else:
            # Mostrar status do dashboard
            print("Dashboard não está rodando")
            print(f"Para iniciar: penin dashboard --serve --port {args.port}")
            return 0


def create_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos"""
    parser = argparse.ArgumentParser(
        prog="penin",
        description="PENIN-Ω Auto-Evolution System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  penin evolve --n 8 --budget 1.0 --provider openai
  penin evaluate --model gpt-4 --suite basic --save
  penin promote --run cycle_12345678
  penin rollback --to LAST_GOOD
  penin dashboard --serve --port 8000
  penin status --verbose
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: evolve
    evolve_parser = subparsers.add_parser("evolve", help="Executar ciclo de evolução")
    evolve_parser.add_argument("--n", "--n-challengers", dest="n_challengers",
                              type=int, default=6, help="Número de challengers")
    evolve_parser.add_argument("--budget", type=float, default=1.0,
                              help="Budget em USD")
    evolve_parser.add_argument("--provider", default="mock",
                              help="ID do provider")
    evolve_parser.add_argument("--dry-run", action="store_true",
                              help="Dry run (só mutação)")
    evolve_parser.add_argument("--no-tuning", action="store_true",
                              help="Desabilitar auto-tuning")
    evolve_parser.add_argument("--no-canary", action="store_true",
                              help="Desabilitar testes canário")
    evolve_parser.add_argument("--batch", type=int,
                              help="Executar batch de N ciclos")

    # Comando: evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Avaliar modelo")
    eval_parser.add_argument("--model", required=True,
                            help="Modelo para avaliar")
    eval_parser.add_argument("--suite", default="basic",
                            choices=["basic", "full", "custom"],
                            help="Suíte de avaliação")
    eval_parser.add_argument("--save", action="store_true",
                            help="Salvar resultado em arquivo")

    # Comando: promote
    promote_parser = subparsers.add_parser("promote", help="Promover run para champion")
    promote_parser.add_argument("--run", dest="run_id", required=True,
                               help="ID do run para promover")

    # Comando: rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback champion")
    rollback_parser.add_argument("--to", dest="target", default="LAST_GOOD",
                                help="Target do rollback (run_id ou LAST_GOOD)")

    # Comando: status
    status_parser = subparsers.add_parser("status", help="Status do sistema")
    status_parser.add_argument("--verbose", "-v", action="store_true",
                              help="Output verboso")

    # Comando: dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Dashboard de observabilidade")
    dashboard_parser.add_argument("--serve", action="store_true",
                                 help="Iniciar servidor")
    dashboard_parser.add_argument("--port", type=int, default=8000,
                                 help="Porta do servidor")
    dashboard_parser.add_argument("--auth-token",
                                 help="Token de autenticação")

    return parser


def main():
    """Função principal do CLI"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Banner
    print("🧠 PENIN-Ω Auto-Evolution System v7.0")
    print("   Deterministic • Fail-Closed • Auditable")
    print()

    # Inicializar CLI
    try:
        cli = PeninCLI()
    except Exception as e:
        print(f"❌ Erro ao inicializar CLI: {e}")
        return 1

    # Executar comando
    try:
        if args.command == "evolve":
            return cli.cmd_evolve(args)
        elif args.command == "evaluate":
            return cli.cmd_evaluate(args)
        elif args.command == "promote":
            return cli.cmd_promote(args)
        elif args.command == "rollback":
            return cli.cmd_rollback(args)
        elif args.command == "status":
            return cli.cmd_status(args)
        elif args.command == "dashboard":
            return cli.cmd_dashboard(args)
        else:
            print(f"❌ Comando desconhecido: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        return 130
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
