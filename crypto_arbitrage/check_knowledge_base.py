"""检查知识库状态脚本"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from knowledge.knowledge_graph_memo0_storage import KnowledgeGraphMemo0Storage
    from knowledge.reasoning_history_memo0_storage import ReasoningHistoryMemo0Storage

    print("=" * 80)
    print("知识库状态检查")
    print("=" * 80)

    # 检查知识图谱存储
    print("\n[1] 知识图谱存储检查:")
    try:
        kg_storage = KnowledgeGraphMemo0Storage()
        print(f"    数据库文件: {kg_storage.db_path}")
        print(f"    文件存在: {os.path.exists(kg_storage.db_path)}")

        # 尝试获取统计信息
        try:
            # 获取节点数量
            nodes = kg_storage.get_all_nodes()
            print(f"    节点数量: {len(nodes)}")

            # 获取关系数量
            relations = kg_storage.get_all_relations()
            print(f"    关系数量: {len(relations)}")

            # 按类型统计
            node_types = {}
            for node in nodes:
                node_type = node.get('node_type', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1

            print("    节点类型分布:")
            for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
                print(f"      - {node_type}: {count}")

        except Exception as e:
            print(f"    [警告] 获取统计信息失败: {e}")

    except Exception as e:
        print(f"    [错误] 知识图谱存储初始化失败: {e}")

    # 检查推理历史存储
    print("\n[2] 推理历史存储检查:")
    try:
        rh_storage = ReasoningHistoryMemo0Storage()
        print(f"    数据库文件: {rh_storage.db_path}")
        print(f"    文件存在: {os.path.exists(rh_storage.db_path)}")

        # 尝试获取统计信息
        try:
            # 获取推理历史记录数
            history_records = rh_storage.get_all_reasoning_history()
            print(f"    推理历史记录数: {len(history_records)}")

            # 获取推理链记录数
            chain_records = rh_storage.get_all_reasoning_chains()
            print(f"    推理链记录数: {len(chain_records)}")

        except Exception as e:
            print(f"    [警告] 获取统计信息失败: {e}")

    except Exception as e:
        print(f"    [错误] 推理历史存储初始化失败: {e}")

    print("\n" + "=" * 80)
    print("知识库状态检查完成")
    print("=" * 80)

except ImportError as e:
    print(f"[错误] 无法导入知识库模块: {e}")
    print("[提示] 请确保 knowledge 目录存在且包含必要的模块")
except Exception as e:
    print(f"[错误] 检查过程中出现异常: {e}")
    import traceback
    traceback.print_exc()
