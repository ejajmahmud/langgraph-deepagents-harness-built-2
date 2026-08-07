#!/usr/bin/env python3
"""合并AST提取结果"""

import json
from pathlib import Path

def main():
    # 读取各模块的AST结果
    trading = json.loads(Path('trading_ast.json').read_text())
    strategies = json.loads(Path('strategies_ast.json').read_text())
    storage = json.loads(Path('storage_ast.json').read_text())
    agents = json.loads(Path('agents_ast.json').read_text())

    # 合并节点和边
    all_nodes = trading['nodes'] + strategies['nodes'] + storage['nodes'] + agents['nodes']
    all_edges = trading['edges'] + strategies['edges'] + storage['edges'] + agents['edges']

    # 去重节点
    seen = set()
    deduped_nodes = []
    for n in all_nodes:
        if n['id'] not in seen:
            seen.add(n['id'])
            deduped_nodes.append(n)

    # 构建最终合并结果
    merged = {
        'nodes': deduped_nodes,
        'edges': all_edges,
        'input_tokens': 0,
        'output_tokens': 0
    }

    # 写入最终文件
    Path('.graphify_extract.json').write_text(json.dumps(merged, indent=2))
    print(f'合并完成: {len(deduped_nodes)} 节点, {len(all_edges)} 边')
    print(f'原始节点数: {len(all_nodes)}, 去重后: {len(deduped_nodes)}')

    # 统计信息
    print('\n模块统计:')
    print(f'  Trading: {len(trading["nodes"])} 节点, {len(trading["edges"])} 边')
    print(f'  Strategies: {len(strategies["nodes"])} 节点, {len(strategies["edges"])} 边')
    print(f'  Storage: {len(storage["nodes"])} 节点, {len(storage["edges"])} 边')
    print(f'  Agents: {len(agents["nodes"])} 节点, {len(agents["edges"])} 边')

if __name__ == '__main__':
    main()