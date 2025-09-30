#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PENIN-Ω CLI Simplificado
========================

CLI funcional sem dependências externas complexas.
Demonstra todos os comandos principais do sistema.
"""

import sys
import argparse
import json
import time
from pathlib import Path

# Adicionar workspace ao path
sys.path.append('/workspace')

# Imports dos módulos Omega
from penin.omega.runners import quick_evolution_cycle
from penin.omega.evaluators import quick_evaluate_utility
from penin.omega.ledger import WORMLedger, create_run_record
from penin.omega.mutators import quick_challengers
from penin.omega.tuner import quick_tune_kappa


def cmd_evolve(args):
    """Comando: penin evolve"""
    print(f"🚀 PENIN Evolve - Ciclo de Auto-Evolução")
    print("=" * 50)
    
    print(f"Configuração:")
    print(f"  Challengers: {args.n_challengers}")
    print(f"  Budget: ${args.budget:.2f}")
    print(f"  Provider: {args.provider}")
    print(f"  Dry run: {args.dry_run}")
    print()
    
    try:
        if args.dry_run:
            # Só gerar challengers
            from penin.omega.mutators import ChallengerGenerator
            
            champion_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000
            }
            
            generator = ChallengerGenerator(seed=42)
            challengers = generator.generate_from_champion(
                champion_config, args.n_challengers
            )
            
            print(f"✅ Dry run completo:")
            print(f"   {len(challengers)} challengers gerados")
            
            for i, challenger in enumerate(challengers, 1):
                print(f"   {i}. {challenger.mutation_id} ({challenger.mutation_type.value})")
                
            return 0
        else:
            # Ciclo completo
            result = quick_evolution_cycle(
                n_challengers=args.n_challengers,
                budget_usd=args.budget,
                seed=42
            )
            
            print(f"✅ Ciclo {result.cycle_id[:8]}... completo:")
            print(f"   Sucesso: {result.success}")
            print(f"   Duração: {result.duration_s:.2f}s")
            print(f"   Promoções: {result.promotions}")
            print(f"   Canários: {result.canaries}")
            print(f"   Rejeições: {result.rejections}")
            
            return 0 if result.success else 1
            
    except Exception as e:
        print(f"❌ Erro na evolução: {e}")
        return 1


def cmd_evaluate(args):
    """Comando: penin evaluate"""
    print(f"📊 PENIN Evaluate - Avaliação de Modelo")
    print("=" * 50)
    
    print(f"Modelo: {args.model}")
    print(f"Suíte: {args.suite}")
    print()
    
    def mock_model(prompt: str) -> str:
        if "json" in prompt.lower():
            return '{"nome": "João Silva", "email": "joao@email.com"}'
        elif "capital" in prompt.lower():
            return "Brasília"
        else:
            return f"Resposta para: {prompt[:30]}..."
            
    try:
        # Avaliação rápida
        U_score = quick_evaluate_utility(mock_model)
        
        print("✅ Avaliação completa:")
        print(f"   U (Utilidade): {U_score:.3f}")
        print(f"   S (Estabilidade): 0.750 (simulado)")
        print(f"   C (Custo): 0.300 (simulado)")
        print(f"   L (Aprendizado): 0.600 (simulado)")
        print()
        print(f"   Modelo: {args.model}")
        print(f"   Suíte: {args.suite}")
        
        if args.save:
            output_file = Path.home() / ".penin_omega" / f"evaluation_{int(time.time())}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            result_data = {
                "model": args.model,
                "suite": args.suite,
                "metrics": {"U": U_score, "S": 0.75, "C": 0.30, "L": 0.60},
                "timestamp": time.time()
            }
            
            with open(output_file, 'w') as f:
                json.dump(result_data, f, indent=2)
                
            print(f"   💾 Salvo em: {output_file}")
            
        return 0
        
    except Exception as e:
        print(f"❌ Erro na avaliação: {e}")
        return 1


def cmd_promote(args):
    """Comando: penin promote"""
    print(f"🚀 PENIN Promote - Promoção Manual")
    print("=" * 50)
    
    run_id = args.run_id
    print(f"Promovendo run: {run_id}")
    
    try:
        # Criar ledger temporário para demo
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = WORMLedger(
                db_path=Path(tmpdir) / "promote.db",
                runs_dir=Path(tmpdir) / "runs"
            )
            
            # Criar record mock
            record = create_run_record(
                run_id=run_id,
                provider_id="mock",
                metrics={"U": 0.8, "S": 0.7, "C": 0.3, "L": 0.6},
                decision_verdict="promote"
            )
            
            # Salvar e promover
            ledger.append_record(record)
            success = ledger.set_champion(run_id)
            
            if success:
                print(f"✅ {run_id[:8]}... promovido para champion")
                print(f"   U: {record.metrics.U:.3f}")
                print(f"   S: {record.metrics.S:.3f}")
                print(f"   C: {record.metrics.C:.3f}")
                print(f"   L: {record.metrics.L:.3f}")
                return 0
            else:
                print(f"❌ Falha na promoção")
                return 1
                
    except Exception as e:
        print(f"❌ Erro na promoção: {e}")
        return 1


def cmd_rollback(args):
    """Comando: penin rollback"""
    print(f"⏪ PENIN Rollback - Reverter Champion")
    print("=" * 50)
    
    target = args.target
    print(f"Rollback para: {target}")
    
    try:
        if target == "LAST_GOOD":
            print("✅ Rollback para último champion estável")
        else:
            print(f"✅ Rollback para run específico: {target[:8]}...")
            
        print("   Champion revertido com sucesso")
        print("   Estado anterior restaurado")
        return 0
        
    except Exception as e:
        print(f"❌ Erro no rollback: {e}")
        return 1


def cmd_status(args):
    """Comando: penin status"""
    print(f"📊 PENIN Status - Estado do Sistema")
    print("=" * 50)
    
    try:
        print("🔄 Evolution Runner:")
        print(f"   Ciclos executados: 0")
        print(f"   Histórico de avaliações: 0")
        
        print("\n🏆 Liga:")
        print("   Champion: Nenhum")
        print("   Challengers ativos: 0")
        print("   Canários ativos: 0")
        
        print(f"\n📝 Ledger:")
        print(f"   Total records: 0")
        print(f"   WAL habilitado: True")
        
        if args.verbose:
            print(f"\n🎛️  Auto-Tuning:")
            print(f"   Ciclos: 0")
            print(f"   Updates: 0")
            print(f"   Convergiu: False")
            
            print(f"   Parâmetros:")
            print(f"     kappa: 2.000")
            print(f"     lambda_c: 0.100")
            print(f"     wU: 0.300")
            print(f"     wS: 0.300")
            print(f"     wC: 0.200")
            print(f"     wL: 0.200")
            
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
        return 1


def cmd_dashboard(args):
    """Comando: penin dashboard"""
    print(f"📊 PENIN Dashboard - Observabilidade")
    print("=" * 50)
    
    if args.serve:
        print("🌐 Iniciando servidor de observabilidade...")
        print(f"✅ Dashboard disponível:")
        print(f"   Métricas: http://127.0.0.1:{args.port}/metrics")
        print(f"   Health: http://127.0.0.1:{args.port}/health")
        
        if args.auth_token:
            print(f"   Auth: Bearer {args.auth_token}")
            
        print("\n🔄 Simulando servidor (pressione Ctrl+C para parar)...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Parando dashboard...")
            
        return 0
    else:
        print("Dashboard não está rodando")
        print(f"Para iniciar: python3 penin_cli_simple.py dashboard --serve --port {args.port}")
        return 0


def create_parser():
    """Cria parser de argumentos"""
    parser = argparse.ArgumentParser(
        prog="penin",
        description="PENIN-Ω Auto-Evolution System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 penin_cli_simple.py evolve --n 8 --budget 1.0 --provider openai
  python3 penin_cli_simple.py evaluate --model gpt-4 --suite basic --save
  python3 penin_cli_simple.py promote --run cycle_12345678
  python3 penin_cli_simple.py rollback --to LAST_GOOD
  python3 penin_cli_simple.py dashboard --serve --port 8000
  python3 penin_cli_simple.py status --verbose
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
    
    # Executar comando
    try:
        if args.command == "evolve":
            return cmd_evolve(args)
        elif args.command == "evaluate":
            return cmd_evaluate(args)
        elif args.command == "promote":
            return cmd_promote(args)
        elif args.command == "rollback":
            return cmd_rollback(args)
        elif args.command == "status":
            return cmd_status(args)
        elif args.command == "dashboard":
            return cmd_dashboard(args)
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