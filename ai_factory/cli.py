"""Simple local CLI for AI Factory OS.

Run with:
    python -m ai_factory.cli
"""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from ai_factory.agents.founder_agent import (
    founder_dashboard,
    founder_inventory_report,
    founder_task_report,
    generate_founder_recommendations,
    schedule_founder_task,
    schedule_analytics_refresh,
    schedule_batch_generation,
    schedule_generate_designs,
    schedule_niche_research,
)
from ai_factory.agents.founder_intelligence import (
    generate_growth_opportunities,
    generate_pipeline_bottlenecks,
    generate_risk_report,
)
from ai_factory.agents.founder_briefing import (
    generate_biggest_risks,
    generate_cleanup_priorities,
    generate_daily_briefing,
    generate_inventory_alerts,
    generate_top_opportunities,
    generate_execution_recommendation,
    generate_repair_recommendations,
)
from ai_factory.agents.founder_decision_center import (
    generate_daily_execution_plan,
    generate_inventory_cleanup_plan,
    generate_revenue_priority_actions,
    generate_scaling_readiness_report,
    generate_weekly_focus,
)
from ai_factory.analytics.kpi_tracker import track_kpis
from ai_factory.analytics.profitability_engine import top_profitable_products, worst_products
from ai_factory.analytics.operational_scorecard import generate_operational_scorecard
from ai_factory.analytics.revenue_tracker import generate_revenue_report, record_sale
from ai_factory.analytics.workflow_analytics import workflow_completion_distribution, workflow_success_rate
from ai_factory.analytics.performance_snapshots import create_performance_snapshot
from ai_factory.maintenance.backup_manager import create_backup_snapshot, list_backups, restore_backup
from ai_factory.maintenance.csv_health import summarize_csv_health
from ai_factory.tasks.audit_log import SYSTEM_LOG
from ai_factory.tasks.task_runner import run_next_task
from ai_factory.workflows.workflow_engine import create_batch_workflow, create_design_workflow, get_workflow_history
from ai_factory.intelligence.historical_learning import generate_learning_summary
from ai_factory.intelligence.priority_engine import generate_priority_queue
from ai_factory.intelligence.trend_score import (
    calculate_product_trend_score,
    cluster_products_by_topic,
    detect_niche_saturation,
    generate_product_intelligence,
    import_trend_csv,
    load_trend_data,
    recommend_higher_performing_niches,
    score_all_products,
    score_listing_completeness,
    score_tag_quality,
    score_title_quality,
)
from ai_factory.intelligence.revenue_optimizer import (
    recommend_batch_sizes,
    recommend_best_niches,
    recommend_listing_improvements,
    recommend_products_to_archive,
)
from ai_factory.quality.quality_evolution import generate_quality_summary
from ai_factory.maintenance.inventory_hygiene import generate_inventory_hygiene_report
from ai_factory.intelligence.product_selector import select_products_for_listing
from ai_factory.listings.etsy_readiness import evaluate_etsy_readiness, generate_readiness_report
from ai_factory.listings.etsy_metrics_importer import compare_listing_performance, import_listing_metrics
from ai_factory.listings.etsy_seo_optimizer import score_seo_strength, suggest_keyword_expansion
from ai_factory.importers.etsy_shop_importer import import_existing_etsy_listings
from ai_factory.intelligence.factory_recommendations import generate_factory_recommendations
from ai_factory.intelligence.listing_health import summarize_listing_health
from ai_factory.etsy.etsy_upload import (
    cleanup_completed_etsy_upload_queue,
    export_etsy_upload_queue_packages,
    get_etsy_upload_queue_report,
    list_etsy_upload_queue,
    process_etsy_upload_queue,
    queue_etsy_upload,
    retry_failed_etsy_upload,
)
from ai_factory.listings.listing_change_history import record_listing_change, summarize_listing_changes
from ai_factory.listings.listing_packager import export_listing_package
from ai_factory.listings.listing_tracker import create_listing_record, generate_listing_report, read_listings, update_listing_metrics, update_thumbnail_test
from ai_factory.research.etsy_listing_research import generate_niche_research_summary, record_competitor_observation
from ai_factory.production.batch_manager import rank_batches
from ai_factory.signals.product_signal_engine import rank_niches_by_signal, rank_products_by_signal
from ai_factory.signals.market_signal_ingestor import generate_market_signal_report
from ai_factory.signals.validation_score import generate_validation_report, rank_validated_products
from ai_factory.snapshots.state_snapshot import create_state_snapshot
from ai_factory.mockups.mockup_generator import generate_mockup_set, score_mockup_quality
from ai_factory.products.listing_generator import score_listing_quality
from ai_factory.products.product_manager import read_products
from ai_factory.review.design_improvement import analyze_design_weaknesses, suggest_design_improvements
from ai_factory.workflows.product_repair_workflow import create_product_repair_workflow
from ai_factory.agents.daily_execution_brief import generate_daily_execution_brief
from ai_factory.signals.thumbnail_analyzer import analyze_thumbnail_performance
from ai_factory.variants.emotional_variant_generator import generate_emotional_variants, suggest_cluster_variants
from ai_factory.analytics.profit_calculator import estimate_total_profit
from ai_factory.intelligence.winning_pattern_detector import detect_winning_patterns
from ai_factory.agents.weekly_founder_review import generate_weekly_founder_review
from ai_factory.visuals.factory_map import build_factory_map


def _prompt_keywords() -> list[str]:
    raw = input("Keywords, comma-separated: ").strip()
    return [item.strip() for item in raw.split(",") if item.strip()]


def _print_created(task_id: str) -> None:
    print(f"Created task: {task_id}")


def _print_recommendations() -> None:
    print("\n=== FOUNDER RECOMMENDATIONS ===")
    for index, recommendation in enumerate(generate_founder_recommendations(), start=1):
        print(f"{index}. [{recommendation['priority']}] {recommendation['action']}")
        print(f"   Task: {recommendation['task_type']} Payload: {recommendation['payload']}")


def _tail_audit_log(lines: int = 20) -> None:
    if not SYSTEM_LOG.exists():
        print("No audit log yet.")
        return
    content = SYSTEM_LOG.read_text(encoding="utf-8").splitlines()
    for line in content[-lines:]:
        print(line)


def _print_workflow_history() -> None:
    print("\n=== WORKFLOW HISTORY ===")
    for row in get_workflow_history()[-10:]:
        print(f"{row['workflow_id']} {row['workflow_type']} {row['status']} tasks={row['task_count']}")


def _open_path_in_browser(path: str) -> None:
    resolved = Path(path).expanduser().resolve()
    try:
        webbrowser.open(resolved.as_uri(), new=2)
        print("Opened factory map in browser.")
    except Exception:
        if sys.platform == "darwin":
            subprocess.run(["open", str(resolved)], check=False)
        elif sys.platform == "win32":
            try:
                os.startfile(str(resolved))  # type: ignore[attr-defined]
            except Exception:
                pass
        else:
            subprocess.run(["xdg-open", str(resolved)], check=False)
        print("Attempted to open the factory map in the default browser.")


def _print_profitability_report() -> None:
    print("\n=== PROFITABILITY REPORT ===")
    print("Top products:")
    for item in top_profitable_products(limit=5):
        print(item)
    print("Worst products:")
    for item in worst_products(limit=5):
        print(item)


def _get_product(product_id: str) -> dict[str, str]:
    for product in read_products():
        if product.get("id") == product_id:
            return product
    raise ValueError(f"Product id not found: {product_id}")


def _product_design_path(product: dict[str, str]) -> str:
    return product.get("image_path") or product.get("filename") or ""


def run_cli() -> None:
    """Run the local terminal menu."""
    while True:
        print("\n=== AI FACTORY OS ===")
        print("1. Founder dashboard")
        print("2. Inventory report")
        print("3. Task report")
        print("4. Run next task (dry run)")
        print("5. Run next task (real)")
        print("6. Schedule niche research")
        print("7. Schedule design generation")
        print("8. Schedule analytics refresh")
        print("9. Review product")
        print("10. Create variant")
        print("11. View recommendations")
        print("12. CSV health check")
        print("13. Create backup")
        print("14. Restore backup")
        print("15. View audit log tail")
        print("16. Schedule batch generation")
        print("17. Create performance snapshot")
        print("18. Create design workflow")
        print("19. Create batch workflow")
        print("20. View workflow history")
        print("21. View profitability report")
        print("22. View bottleneck report")
        print("23. View growth opportunities")
        print("24. View risk report")
        print("25. View top products")
        print("26. View worst products")
        print("27. View learning summary")
        print("28. View revenue optimization report")
        print("29. View quality evolution report")
        print("30. Create operational snapshot")
        print("31. View KPI report")
        print("32. View scaling readiness")
        print("33. View execution plan")
        print("34. View inventory cleanup plan")
        print("35. View signal rankings")
        print("36. View priority queue")
        print("37. View operational scorecard")
        print("38. View founder briefing")
        print("39. View inventory hygiene report")
        print("40. Create experiment")
        print("41. View experiment summary")
        print("42. View top batches")
        print("43. View weakest batches")
        print("44. Create listing record")
        print("45. Update listing metrics")
        print("46. Record sale")
        print("47. View validation rankings")
        print("48. View real revenue report")
        print("49. View market signal report")
        print("50. View strongest validated products")
        print("51. View products needing cleanup")
        print("52. Select best products for upload")
        print("53. Etsy readiness check")
        print("54. Export listing package")
        print("55. Record competitor observation")
        print("56. View early winners")
        print("57. View upload recommendations")
        print("58. Analyze product weaknesses")
        print("59. Suggest product improvements")
        print("60. Generate improved mockup set")
        print("61. Score listing quality")
        print("62. Create repair workflow")
        print("63. View repair recommendations")
        print("64. Import Etsy metrics")
        print("65. Compare listing performance")
        print("66. Analyze thumbnail performance")
        print("67. Generate emotional variants")
        print("68. Score Etsy SEO")
        print("69. View daily execution brief")
        print("70. Update thumbnail test")
        print("71. Record listing change")
        print("72. View listing change history")
        print("73. Estimate profit")
        print("74. Detect winning patterns")
        print("75. Suggest product cluster variants")
        print("76. Weekly Founder review")
        print("77. Build HomeBase Factory Map and open it in browser")
        print("78. Import existing Etsy shop listings from export CSV")
        print("79. View listing health report")
        print("80. View recommendation engine report")
        print("81. Queue Etsy upload-ready products")
        print("82. Run Etsy upload queue")
        print("83. Inspect Etsy upload queue")
        print("84. Retry failed Etsy queue items")
        print("85. Cleanup completed Etsy queue items")
        print("86. Export queued Etsy listing packages")
        print("87. Import market trend CSV")
        print("88. Score products with trend intelligence")
        print("89. Inspect product intelligence")
        print("90. View niche saturation and clusters")
        print("91. Rebuild Etsy sync dashboard")
        print("92. Force Full Factory Sync")
        print("93. Exit")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                founder_dashboard()
            elif choice == "2":
                founder_inventory_report()
            elif choice == "3":
                founder_task_report()
            elif choice == "4":
                print(run_next_task(dry_run=True))
            elif choice == "5":
                confirm = input("Real run may call OpenAI or local upload markers. Type RUN: ").strip()
                if confirm == "RUN":
                    print(run_next_task(dry_run=False))
                else:
                    print("Cancelled real run.")
            elif choice == "6":
                _print_created(schedule_niche_research(_prompt_keywords()))
            elif choice == "7":
                niche = input("Niche: ").strip()
                amount = int(input("Amount: ").strip())
                _print_created(schedule_generate_designs(niche, amount))
            elif choice == "8":
                _print_created(schedule_analytics_refresh())
            elif choice == "9":
                product_id = input("Product id to review: ").strip()
                _print_created(schedule_founder_task("review_product", payload={"product_id": product_id}))
            elif choice == "10":
                product_id = input("Product id to variant: ").strip()
                variant_type = input("Variant type (color/text/style): ").strip() or "style"
                _print_created(
                    schedule_founder_task(
                        "create_variant",
                        payload={"product_id": product_id, "variant_type": variant_type},
                    )
                )
            elif choice == "11":
                _print_recommendations()
            elif choice == "12":
                print(summarize_csv_health())
            elif choice == "13":
                print(f"Backup created: {create_backup_snapshot()}")
            elif choice == "14":
                backups = list_backups()
                if not backups:
                    print("No backups found.")
                    continue
                for index, backup in enumerate(backups, start=1):
                    print(f"{index}. {backup.name}")
                selected = int(input("Restore which backup number?: ").strip())
                confirm = input("Type RESTORE to overwrite current CSV files: ").strip()
                if confirm == "RESTORE":
                    print(restore_backup(backups[selected - 1], confirm=True))
                else:
                    print("Restore cancelled.")
            elif choice == "15":
                _tail_audit_log()
            elif choice == "16":
                niche = input("Batch niche: ").strip()
                amount = int(input("Amount: ").strip())
                _print_created(schedule_batch_generation(niche, amount))
            elif choice == "17":
                print(f"Snapshot created: {create_performance_snapshot()}")
            elif choice == "18":
                niche = input("Workflow niche: ").strip()
                amount = int(input("Amount: ").strip())
                print(create_design_workflow(niche=niche, amount=amount, dry_run=False))
            elif choice == "19":
                niche = input("Batch workflow niche: ").strip()
                amount = int(input("Amount: ").strip())
                print(create_batch_workflow(niche=niche, amount=amount, dry_run=False))
            elif choice == "20":
                _print_workflow_history()
            elif choice == "21":
                _print_profitability_report()
            elif choice == "22":
                print(generate_pipeline_bottlenecks())
                print({"workflow_success_rate": workflow_success_rate(), "distribution": workflow_completion_distribution()})
            elif choice == "23":
                print(generate_growth_opportunities())
            elif choice == "24":
                print(generate_risk_report())
            elif choice == "25":
                print(top_profitable_products(limit=10))
            elif choice == "26":
                print(worst_products(limit=10))
            elif choice == "27":
                print(generate_learning_summary())
            elif choice == "28":
                print(
                    {
                        "best_niches": recommend_best_niches(),
                        "batch_sizes": recommend_batch_sizes(),
                        "listing_improvements": recommend_listing_improvements(),
                        "archive_candidates": recommend_products_to_archive(),
                        "revenue_actions": generate_revenue_priority_actions(),
                    }
                )
            elif choice == "29":
                print(generate_quality_summary())
            elif choice == "30":
                print(f"Operational snapshot: {create_state_snapshot()}")
            elif choice == "31":
                print(track_kpis())
            elif choice == "32":
                print(generate_scaling_readiness_report())
            elif choice == "33":
                print({"daily": generate_daily_execution_plan(), "weekly": generate_weekly_focus()})
            elif choice == "34":
                print(generate_inventory_cleanup_plan())
            elif choice == "35":
                print({"products": rank_products_by_signal()[:10], "niches": rank_niches_by_signal()[:10]})
            elif choice == "36":
                print(generate_priority_queue()[:20])
            elif choice == "37":
                print(generate_operational_scorecard())
            elif choice == "38":
                print(generate_daily_briefing())
                print({"alerts": generate_inventory_alerts(), "opportunities": generate_top_opportunities(), "risks": generate_biggest_risks(), "cleanup": generate_cleanup_priorities()})
            elif choice == "39":
                print(generate_inventory_hygiene_report())
            elif choice == "40":
                from ai_factory.experiments.experiment_tracker import create_experiment

                experiment_type = input("Experiment type: ").strip()
                control = input("Control product ids, comma-separated: ").strip().split(",")
                test = input("Test product ids, comma-separated: ").strip().split(",")
                print(create_experiment(experiment_type, [x.strip() for x in control if x.strip()], [x.strip() for x in test if x.strip()]))
            elif choice == "41":
                from ai_factory.experiments.experiment_tracker import generate_experiment_summary

                print(generate_experiment_summary())
            elif choice == "42":
                print(rank_batches()[:10])
            elif choice == "43":
                print(list(reversed(rank_batches()))[:10])
            elif choice == "44":
                product_id = input("Product id: ").strip()
                platform = input("Platform (etsy): ").strip() or "etsy"
                url = input("Listing URL (optional): ").strip()
                print(create_listing_record(product_id, platform=platform, listing_url=url))
            elif choice == "45":
                listing_id = input("Listing id: ").strip()
                views = int(input("Views: ").strip() or "0")
                favorites = int(input("Favorites: ").strip() or "0")
                orders = int(input("Orders: ").strip() or "0")
                revenue = float(input("Revenue: ").strip() or "0")
                print(update_listing_metrics(listing_id, views=views, favorites=favorites, orders=orders, revenue=revenue))
            elif choice == "46":
                product_id = input("Product id: ").strip()
                listing_id = input("Listing id (optional): ").strip()
                revenue = float(input("Revenue: ").strip() or "0")
                print(record_sale(product_id, listing_id=listing_id, revenue=revenue))
            elif choice == "47":
                print(generate_validation_report())
            elif choice == "48":
                print(generate_revenue_report())
            elif choice == "49":
                print(generate_market_signal_report())
            elif choice == "50":
                print(rank_validated_products()[:10])
            elif choice == "51":
                print(generate_inventory_hygiene_report())
            elif choice == "52":
                print(select_products_for_listing(limit=5))
            elif choice == "53":
                product_id = input("Product id (blank for all): ").strip()
                print(evaluate_etsy_readiness(product_id) if product_id else generate_readiness_report())
            elif choice == "54":
                product_id = input("Product id: ").strip()
                print(f"Exported: {export_listing_package(product_id)}")
            elif choice == "55":
                niche = input("Niche: ").strip()
                title = input("Competitor title: ").strip()
                price = input("Price observation: ").strip()
                keywords = input("Keyword observation: ").strip()
                style = input("Style observation: ").strip()
                saturation = input("Saturation notes: ").strip()
                print(record_competitor_observation(niche=niche, competitor_title=title, price_observation=price, keyword_observation=keywords, style_observation=style, market_saturation_notes=saturation))
            elif choice == "56":
                from ai_factory.signals.early_win_detector import detect_early_winners

                print(detect_early_winners())
            elif choice == "57":
                print(generate_execution_recommendation())
            elif choice == "58":
                product_id = input("Product id: ").strip()
                print(analyze_design_weaknesses(product_id))
            elif choice == "59":
                product_id = input("Product id: ").strip()
                print(suggest_design_improvements(product_id))
            elif choice == "60":
                product_id = input("Product id: ").strip()
                product = _get_product(product_id)
                design_path = input("Design path (blank to use product image): ").strip() or _product_design_path(product)
                result = generate_mockup_set(int(product_id), design_path)
                print(result)
                print({"mockup_quality": score_mockup_quality(result["mockup_paths"])})
            elif choice == "61":
                product_id = input("Product id: ").strip()
                print(score_listing_quality(_get_product(product_id)))
            elif choice == "62":
                product_id = input("Product id: ").strip()
                dry = input("Dry run? (Y/n): ").strip().lower() != "n"
                print(create_product_repair_workflow(product_id, dry_run=dry))
            elif choice == "63":
                print(generate_repair_recommendations())
            elif choice == "64":
                listing_id = input("Listing id: ").strip()
                views = input("Views: ").strip()
                favorites = input("Favorites: ").strip()
                orders = input("Orders: ").strip()
                revenue = input("Revenue: ").strip()
                notes = input("Notes / thumbnail style: ").strip()
                print(import_listing_metrics(listing_id, views=views, favorites=favorites, orders=orders, revenue=revenue, notes=notes or None))
            elif choice == "65":
                print(compare_listing_performance())
            elif choice == "66":
                print(analyze_thumbnail_performance())
            elif choice == "67":
                base = input("Base concept: ").strip() or "Social Anxiety"
                limit = int(input("Variant count: ").strip() or "6")
                print(generate_emotional_variants(base, limit=limit))
            elif choice == "68":
                product_id = input("Product id: ").strip()
                product = _get_product(product_id)
                print(score_seo_strength(product))
                print({"keyword_expansion": suggest_keyword_expansion(product)})
            elif choice == "69":
                print(generate_daily_execution_brief())
            elif choice == "70":
                listing_id = input("Listing id: ").strip()
                style = input("Primary thumbnail style: ").strip()
                version = input("Thumbnail version: ").strip()
                notes = input("Thumbnail test notes: ").strip()
                observations = input("Clickthrough observations: ").strip()
                print(update_thumbnail_test(listing_id, primary_thumbnail_style=style, thumbnail_version=version, thumbnail_test_notes=notes, clickthrough_observations=observations))
            elif choice == "71":
                listing_id = input("Listing id: ").strip()
                print(
                    record_listing_change(
                        listing_id,
                        title_before=input("Title before: ").strip(),
                        title_after=input("Title after: ").strip(),
                        tags_before=input("Tags before: ").strip(),
                        tags_after=input("Tags after: ").strip(),
                        thumbnail_before=input("Thumbnail before: ").strip(),
                        thumbnail_after=input("Thumbnail after: ").strip(),
                        reason_for_change=input("Reason for change: ").strip(),
                    )
                )
            elif choice == "72":
                print(summarize_listing_changes())
            elif choice == "73":
                base_cost = float(input("Printify base cost per order (0 if digital): ").strip() or "0")
                shipping = float(input("Shipping cost per order: ").strip() or "0")
                ads = float(input("Ad spend per listing/default: ").strip() or "0")
                print(estimate_total_profit(default_printify_base_cost=base_cost, default_shipping_cost=shipping, default_ad_spend=ads))
            elif choice == "74":
                print(detect_winning_patterns())
            elif choice == "75":
                base = input("Base concept: ").strip() or "Social Anxiety"
                level = input("Engagement level (emerging/promising/etc): ").strip() or "promising"
                print(suggest_cluster_variants(base, level))
            elif choice == "76":
                print(generate_weekly_founder_review())
            elif choice == "77":
                result = build_factory_map()
                print(f"Factory map ready: {result['output_path']}")
                print({"rooms_detected": result["rooms_detected"], "summary": result["summary"]})
                _open_path_in_browser(result["output_path"])
            elif choice == "78":
                csv_path = input("Etsy export CSV path: ").strip()
                result = import_existing_etsy_listings(csv_path)
                print("Etsy import complete.")
                print(result)
            elif choice == "79":
                print(summarize_listing_health(read_listings()))
            elif choice == "80":
                print(generate_factory_recommendations(read_listings(), read_products()))
            elif choice == "81":
                publish_mode = input("Publish mode (draft/publish) [draft]: ").strip().lower() or "draft"
                result = queue_etsy_upload(publish_mode=publish_mode)
                print("Queued upload-ready Etsy products.")
                print(result)
            elif choice == "82":
                publish_mode = input("Publish mode (draft/publish) [draft]: ").strip().lower() or "draft"
                dry_run = input("Dry run? (y/n) [y]: ").strip().lower() != "n"
                result = process_etsy_upload_queue(dry_run=dry_run, publish_mode=publish_mode)
                print("Etsy upload queue processed.")
                print(result)
            elif choice == "83":
                print("=== Etsy Upload Queue ===")
                print(get_etsy_upload_queue_report())
                for row in list_etsy_upload_queue(limit=20):
                    print(row)
            elif choice == "84":
                result = retry_failed_etsy_upload()
                print("Reset failed Etsy queue items to pending.")
                print(result)
            elif choice == "85":
                result = cleanup_completed_etsy_upload_queue()
                print("Cleaned up completed Etsy queue items.")
                print(result)
            elif choice == "86":
                export_dir = input("Export directory (blank for default): ").strip() or None
                product_filter = input("Product ids to export, comma-separated (blank for all queued): ").strip()
                product_ids = [item.strip() for item in product_filter.split(",") if item.strip()] or None
                result = export_etsy_upload_queue_packages(product_ids=product_ids, export_dir=Path(export_dir) if export_dir else None)
                print("Exported Etsy upload queue packages.")
                print(result)
            elif choice == "87":
                csv_path = input("Trend CSV path: ").strip()
                result = import_trend_csv(csv_path)
                print("Imported trend data.")
                print(result)
            elif choice == "88":
                result = score_all_products(load_trend_data())
                print("Scored all products with trend intelligence.")
                print(result)
            elif choice == "89":
                product_id = input("Product id: ").strip()
                product = _get_product(product_id)
                intelligence = generate_product_intelligence(product, load_trend_data())
                print(f"Product intelligence for {product_id}:")
                print(intelligence)
            elif choice == "90":
                print("=== Niche saturation ===")
                print(detect_niche_saturation())
                print("=== Product clusters ===")
                for cluster in cluster_products_by_topic():
                    print(cluster)
            elif choice == "91":
                result = build_factory_map()
                print(f"Etsy sync dashboard rebuilt: {result['output_path']}")
            elif choice == "92":
                result = build_factory_map()
                print(f"Full Factory Sync complete: {result['output_path']}")
                _open_path_in_browser(result["output_path"])
            elif choice == "93":
                print("Goodbye.")
                return
            else:
                print("Unknown option.")
        except Exception as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    run_cli()
