print("  Type      Pair        Position/Contract     Cost/Savings")
    for ins in instruments:
        pos = ins.get('position') or ins.get('strike') or ins.get('forward') or ins.get('rate', '')
        cost = ins.get('cost') or ins.get('premium') or ''
        print(f"  {ins['type']:8s} {ins['pair']:12s} {pos:>18s} {cost}")