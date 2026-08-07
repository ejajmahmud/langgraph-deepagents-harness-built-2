"""项目进度追踪和迭代记录系统"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from storage.knowledge_base import get_knowledge_base, initialize_knowledge_base

logger = logging.getLogger(__name__)


class ProjectTracker:
    """项目追踪器 - 记录项目进度和迭代历史"""

    def __init__(self, project_name: str = "CryptoArbitrage"):
        """初始化项目追踪器

        Args:
            project_name: 项目名称
        """
        self.project_name = project_name
        self.knowledge_base = get_knowledge_base()

        if not self.knowledge_base:
            logger.warning("知识库未初始化，自动创建默认知识库")
            self.knowledge_base = initialize_knowledge_base()

        logger.info(f"项目追踪器初始化完成: {project_name}")

    def record_iteration(
        self,
        version: str,
        completed_tasks: List[str],
        in_progress_tasks: List[str],
        planned_tasks: List[str],
        summary: str,
        achievements: List[str],
        challenges: List[str],
        next_steps: List[str]
    ) -> None:
        """记录项目迭代

        Args:
            version: 版本号
            completed_tasks: 已完成任务列表
            in_progress_tasks: 进行中任务列表
            planned_tasks: 计划任务列表
            summary: 迭代总结
            achievements: 成就列表
            challenges: 挑战列表
            next_steps: 下一步计划
        """
        date = datetime.now().strftime("%Y-%m-%d")

        # 构建备注说明
        notes = f"## 迭代总结\n\n{summary}\n\n"
        notes += "## 主要成就\n\n"
        for achievement in achievements:
            notes += f"- {achievement}\n"
        notes += "\n## 遇到的挑战\n\n"
        for challenge in challenges:
            notes += f"- {challenge}\n"
        notes += "\n## 下一步计划\n\n"
        for step in next_steps:
            notes += f"- {step}\n"

        # 保存到知识库
        self.knowledge_base.add_project_progress(
            version=version,
            date=date,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            planned_tasks=planned_tasks,
            notes=notes
        )

        logger.info(f"项目迭代已记录: 版本 {version}")

    def get_iteration_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取迭代历史

        Args:
            limit: 返回数量限制

        Returns:
            迭代历史列表
        """
        return self.knowledge_base.get_project_progress_history(limit)

    def generate_progress_report(self) -> str:
        """生成进度报告

        Returns:
            Markdown 格式的进度报告
        """
        iterations = self.get_iteration_history(10)
        if not iterations:
            return "暂无迭代记录"

        report = f"# {self.project_name} 项目进度报告\n\n"
        report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # 最新迭代
        latest = iterations[0]
        report += "## 最新迭代 (V{} - {})\n\n".format(
            latest['version'],
            latest['date']
        )

        if latest['notes']:
            report += f"{latest['notes']}\n\n"

        # 迭代历史
        report += "## 迭代历史\n\n"
        for iteration in iterations:
            version = iteration['version']
            date = iteration['date']

            completed = json.loads(iteration['completed_tasks']) if iteration['completed_tasks'] else []
            in_progress = json.loads(iteration['in_progress_tasks']) if iteration['in_progress_tasks'] else []
            planned = json.loads(iteration['planned_tasks']) if iteration['planned_tasks'] else []

            report += f"### V{version} ({date})\n\n"

            if completed:
                report += "**已完成**:\n\n"
                for task in completed:
                    report += f"- [OK] {task}\n"
                report += "\n"

            if in_progress:
                report += "**进行中**:\n\n"
                for task in in_progress:
                    report += f"- 🔄 {task}\n"
                report += "\n"

            if planned:
                report += "**计划中**:\n\n"
                for task in planned:
                    report += f"- 📋 {task}\n"
                report += "\n"

        return report

    def save_progress_report(self, file_path: str) -> None:
        """保存进度报告到文件

        Args:
            file_path: 文件路径
        """
        report = self.generate_progress_report()

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"进度报告已保存: {file_path}")

    def analyze_progress(self) -> Dict[str, Any]:
        """分析项目进度

        Returns:
            进度分析结果
        """
        iterations = self.get_iteration_history()

        if not iterations:
            return {
                'total_iterations': 0,
                'completion_rate': 0.0,
                'average_tasks_per_iteration': 0.0
            }

        total_iterations = len(iterations)
        total_completed = 0
        total_planned = 0

        for iteration in iterations:
            completed = json.loads(iteration['completed_tasks']) if iteration['completed_tasks'] else []
            planned = json.loads(iteration['planned_tasks']) if iteration['planned_tasks'] else []

            total_completed += len(completed)
            total_planned += len(planned)

        completion_rate = (total_completed / total_planned) if total_planned > 0 else 0.0
        average_tasks_per_iteration = total_completed / total_iterations if total_iterations > 0 else 0.0

        # 分析最新迭代状态
        latest = iterations[0]
        latest_completed = json.loads(latest['completed_tasks']) if latest['completed_tasks'] else []
        latest_in_progress = json.loads(latest['in_progress_tasks']) if latest['in_progress_tasks'] else []

        return {
            'total_iterations': total_iterations,
            'total_completed_tasks': total_completed,
            'total_planned_tasks': total_planned,
            'completion_rate': completion_rate,
            'average_tasks_per_iteration': average_tasks_per_iteration,
            'latest_version': latest['version'],
            'latest_date': latest['date'],
            'latest_completed_count': len(latest_completed),
            'latest_in_progress_count': len(latest_in_progress),
            'is_progress_active': len(latest_in_progress) > 0
        }


# 创建全局项目追踪器实例
project_tracker: Optional[ProjectTracker] = None


def initialize_project_tracker(project_name: str = "CryptoArbitrage") -> ProjectTracker:
    """初始化全局项目追踪器

    Args:
        project_name: 项目名称

    Returns:
        项目追踪器实例
    """
    global project_tracker
    project_tracker = ProjectTracker(project_name)
    return project_tracker


def get_project_tracker() -> Optional[ProjectTracker]:
    """获取全局项目追踪器实例

    Returns:
        项目追踪器实例，如果未初始化则返回 None
    """
    return project_tracker


def record_current_iteration(
    version: str,
    completed_tasks: List[str],
    in_progress_tasks: List[str],
    planned_tasks: List[str],
    summary: str,
    achievements: List[str],
    challenges: List[str],
    next_steps: List[str]
) -> None:
    """记录当前迭代到全局项目追踪器

    Args:
        version: 版本号
        completed_tasks: 已完成任务列表
        in_progress_tasks: 进行中任务列表
        planned_tasks: 计划任务列表
        summary: 迭代总结
        achievements: 成就列表
        challenges: 挑战列表
        next_steps: 下一步计划
    """
    tracker = get_project_tracker()
    if not tracker:
        tracker = initialize_project_tracker()

    tracker.record_iteration(
        version,
        completed_tasks,
        in_progress_tasks,
        planned_tasks,
        summary,
        achievements,
        challenges,
        next_steps
    )
