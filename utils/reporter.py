def generate_report(results_summary, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("# Dataset Generation Summary Report\n\n")
        f.write("## Source Breakdown\n\n")
        f.write("| Source | Item Count |\n")
        f.write("| --- | --- |\n")
        total = 0
        for source, count in results_summary.items():
            f.write(f"| {source} | {count} |\n")
            total += count
        f.write(f"\n**Total Items Collected:** {total}\n\n")
        f.write("## Files Generated\n")
        f.write("- `dataset_gpt_finetune.jsonl`\n")
        f.write("- `dataset_open_source.jsonl`\n")
        f.write("- `dataset_comment_slang.jsonl`\n")
