"""Check project progress and knowledge base status"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.knowledge_base import KnowledgeBase


def main():
    """Check project status"""
    # Set UTF-8 encoding for output
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    print("=== Crypto Trading System Project Status ===\n")

    # Create knowledge base instance
    kb = KnowledgeBase()

    # View project progress
    print("=== Project Progress History ===")
    history = kb.get_project_progress_history(limit=5)
    for h in history:
        completed = eval(h['completed_tasks']) if h['completed_tasks'] else []
        print(f"Version: {h['version']}")
        print(f"Date: {h['date']}")
        print(f"Completed tasks: {len(completed)} items")
        if h['notes']:
            # Handle Unicode characters in notes safely
            try:
                print(f"Notes: {h['notes']}")
            except UnicodeEncodeError:
                print(f"Notes: [Unicode content - check database directly]")
        print("---")

    # View strategies
    print("\n=== Strategy Statistics ===")
    stats = kb.get_statistics()
    print(f"Total strategies: {stats['strategies_count']}")

    # View knowledge entries
    print(f"Knowledge entries: {stats['knowledge_entries_count']}")

    # View trade records
    print(f"Trade records: {stats['trades_count']}")

    # Search recent iteration information
    print("\n=== Recent Iteration Information ===")
    iterations = kb.search_knowledge("iteration", limit=3)
    for iteration in iterations:
        print(f"Title: {iteration['title']}")
        print(f"Category: {iteration['category']}")
        print(f"Importance: {iteration['importance']}")
        print("---")

    print(f"\nTotal profit: ${stats['total_profit']:.2f}")
    print(f"Win rate: {stats['win_rate']:.2%}")


if __name__ == '__main__':
    main()