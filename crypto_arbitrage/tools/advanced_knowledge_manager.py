"""Advanced Knowledge Manager V3.6
Enhanced intelligent knowledge management with advanced extraction and application capabilities.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)


class AdvancedKnowledgeManager:
    """Advanced Knowledge Manager V3.6

    Enhanced capabilities:
    - Advanced pattern recognition in trading data
    - Multi-dimensional knowledge classification
    - Intelligent knowledge graph construction
    - Real-time knowledge quality assessment
    - Predictive knowledge application
    - Cross-strategy knowledge transfer
    """

    def __init__(self, storage_backend=None, config: Dict = None):
        """Initialize Advanced Knowledge Manager V3.6

        Args:
            storage_backend: Knowledge storage backend
            config: Configuration dictionary
        """
        self.storage = storage_backend
        self.config = config or {}

        # Knowledge classification system
        self.knowledge_categories = {
            'market_pattern': ['price_action', 'volume_spike', 'volatility_shift'],
            'trading_strategy': ['entry_signal', 'exit_signal', 'risk_management'],
            'risk_insight': ['correlation_risk', 'liquidity_risk', 'systemic_risk'],
            'performance': ['profit_pattern', 'loss_pattern', 'efficiency_metric'],
            'system': ['error_pattern', 'optimization_opportunity', 'resource_usage']
        }

        # Knowledge quality metrics
        self.quality_factors = {
            'novelty': 0.3,      # Newness of insight
            'accuracy': 0.4,      # Historical accuracy
            'applicability': 0.2,  # Current relevance
            'actionability': 0.1    # How actionable it is
        }

        # Knowledge graph
        self.knowledge_graph = defaultdict(set)
        self.concept_cooccurrence = defaultdict(int)

        # Performance tracking
        self.extraction_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'extraction_accuracy': 0.0,
            'categories_extracted': defaultdict(int)
        }

        # Background processing
        self._processing = False
        self._processing_lock = asyncio.Lock()

        logger.info("Advanced Knowledge Manager V3.6 initialized")

    async def extract_advanced_knowledge(
        self,
        data_source: Dict,
        extraction_mode: str = 'comprehensive'
    ) -> List[Dict]:
        """Extract advanced knowledge from various data sources

        Args:
            data_source: Source data (trade, market, system, etc.)
            extraction_mode: Type of extraction ('comprehensive', 'focused', 'predictive')

        Returns:
            List of extracted knowledge items
        """
        self.extraction_stats['total_extractions'] += 1

        try:
            knowledge_items = []

            # Multi-mode extraction
            if extraction_mode == 'comprehensive':
                knowledge_items.extend(await self._extract_comprehensive_knowledge(data_source))
            elif extraction_mode == 'focused':
                knowledge_items.extend(await self._extract_focused_knowledge(data_source))
            elif extraction_mode == 'predictive':
                knowledge_items.extend(await self._extract_predictive_knowledge(data_source))

            # Enhance knowledge items with quality scores
            for item in knowledge_items:
                item['quality_score'] = self._calculate_quality_score(item)
                item['extraction_timestamp'] = datetime.now().isoformat()
                item['extraction_mode'] = extraction_mode

            # Update statistics
            successful_items = [k for k in knowledge_items if k['quality_score'] > 0.5]
            self.extraction_stats['successful_extractions'] += len(successful_items)

            # Update category statistics
            for item in successful_items:
                category = item.get('category', 'unknown')
                self.extraction_stats['categories_extracted'][category] += 1

            # Update extraction accuracy
            if self.extraction_stats['total_extractions'] > 0:
                self.extraction_stats['extraction_accuracy'] = (
                    self.extraction_stats['successful_extractions'] /
                    self.extraction_stats['total_extractions']
                )

            # Store high-quality knowledge
            for item in successful_items:
                await self._store_knowledge(item)

            # Update knowledge graph
            await self._update_knowledge_graph(knowledge_items)

            logger.info(f"Extracted {len(knowledge_items)} knowledge items, "
                       f"{len(successful_items)} high-quality")

            return successful_items

        except Exception as e:
            logger.error(f"Advanced knowledge extraction failed: {e}")
            return []

    async def _extract_comprehensive_knowledge(self, data_source: Dict) -> List[Dict]:
        """Extract comprehensive knowledge from data"""
        knowledge_items = []

        # Trade data extraction
        if 'trade_data' in data_source:
            knowledge_items.extend(await self._extract_trade_knowledge(data_source['trade_data']))

        # Market data extraction
        if 'market_data' in data_source:
            knowledge_items.extend(await self._extract_market_knowledge(data_source['market_data']))

        # System performance extraction
        if 'performance_data' in data_source:
            knowledge_items.extend(await self._extract_performance_knowledge(data_source['performance_data']))

        # Error data extraction
        if 'error_data' in data_source:
            knowledge_items.extend(await self._extract_error_knowledge(data_source['error_data']))

        return knowledge_items

    async def _extract_focused_knowledge(self, data_source: Dict) -> List[Dict]:
        """Extract focused, high-priority knowledge"""
        knowledge_items = []

        # Focus on high-impact patterns
        if 'trade_data' in data_source:
            trade_knowledge = await self._extract_trade_knowledge(data_source['trade_data'])
            # Filter for high-impact patterns
            knowledge_items.extend([
                k for k in trade_knowledge
                if k.get('importance', 0) > 0.7
            ])

        # Focus on risk insights
        if 'risk_data' in data_source:
            knowledge_items.extend(await self._extract_risk_knowledge(data_source['risk_data']))

        return knowledge_items

    async def _extract_predictive_knowledge(self, data_source: Dict) -> List[Dict]:
        """Extract predictive knowledge for future optimization"""
        knowledge_items = []

        # Pattern prediction
        if 'historical_data' in data_source:
            patterns = await self._analyze_historical_patterns(data_source['historical_data'])
            for pattern in patterns:
                knowledge_items.append({
                    'type': 'predictive_pattern',
                    'content': f"Predictive pattern: {pattern['description']}",
                    'category': 'market_pattern',
                    'confidence': pattern['confidence'],
                    'prediction_horizon': pattern.get('horizon', 'short_term'),
                    'actionable_recommendations': pattern.get('recommendations', [])
                })

        return knowledge_items

    async def _extract_trade_knowledge(self, trade_data: Dict) -> List[Dict]:
        """Extract knowledge from trade data"""
        knowledge_items = []

        # Success pattern analysis
        if trade_data.get('status') == 'completed':
            profit = trade_data.get('actual_profit', 0)
            if profit > 0:
                knowledge_items.append({
                    'type': 'success_pattern',
                    'content': f"Successful trade pattern: {trade_data.get('strategy')} strategy",
                    'category': 'trading_strategy',
                    'profit_amount': profit,
                    'strategy': trade_data.get('strategy'),
                    'execution_time': trade_data.get('execution_time', 0),
                    'importance': min(1.0, profit / 100.0)  # Normalize importance
                })

        # Entry/exit signal analysis
        if 'entry_signal' in trade_data:
            knowledge_items.append({
                'type': 'entry_signal',
                'content': f"Entry signal for {trade_data.get('symbol')}: {trade_data['entry_signal']}",
                'category': 'trading_strategy',
                'symbol': trade_data.get('symbol'),
                'signal_strength': trade_data.get('signal_strength', 0.5)
            })

        return knowledge_items

    async def _extract_market_knowledge(self, market_data: Dict) -> List[Dict]:
        """Extract knowledge from market data"""
        knowledge_items = []

        # Volatility analysis
        if 'volatility' in market_data:
            volatility = market_data['volatility']
            if volatility > 2.0:
                knowledge_items.append({
                    'type': 'volatility_spike',
                    'content': f"High volatility detected: {volatility:.2f}%",
                    'category': 'market_pattern',
                    'volatility_level': volatility,
                    'timestamp': datetime.now().isoformat(),
                    'importance': min(1.0, volatility / 5.0)
                })

        # Volume analysis
        if 'volume' in market_data:
            volume = market_data['volume']
            avg_volume = market_data.get('avg_volume', volume)
            if volume > avg_volume * 1.5:
                knowledge_items.append({
                    'type': 'volume_spike',
                    'content': f"Volume spike detected: {volume:.0f} vs avg {avg_volume:.0f}",
                    'category': 'market_pattern',
                    'volume_ratio': volume / avg_volume,
                    'importance': 0.8
                })

        return knowledge_items

    async def _extract_performance_knowledge(self, performance_data: Dict) -> List[Dict]:
        """Extract knowledge from performance data"""
        knowledge_items = []

        # Profit patterns
        if 'profit_history' in performance_data:
            profits = performance_data['profit_history']
            if len(profits) > 10:
                # Calculate trend
                recent_avg = sum(profits[-5:]) / 5
                older_avg = sum(profits[-10:-5]) / 5

                if recent_avg > older_avg * 1.2:
                    knowledge_items.append({
                        'type': 'profit_trend',
                        'content': f"Improving profit trend: recent ${recent_avg:.2f} vs older ${older_avg:.2f}",
                        'category': 'performance',
                        'trend': 'improving',
                        'improvement_rate': (recent_avg - older_avg) / older_avg,
                        'importance': 0.7
                    })

        # Efficiency metrics
        if 'execution_time' in performance_data and 'profit' in performance_data:
            efficiency = performance_data['profit'] / performance_data['execution_time']
            if efficiency > 0.5:  # $0.5 per second
                knowledge_items.append({
                    'type': 'efficiency_metric',
                    'content': f"High execution efficiency: ${efficiency:.2f}/second",
                    'category': 'performance',
                    'efficiency_score': efficiency,
                    'importance': 0.6
                })

        return knowledge_items

    async def _extract_error_knowledge(self, error_data: Dict) -> List[Dict]:
        """Extract knowledge from error data"""
        knowledge_items = []

        # Error pattern analysis
        if 'error_type' in error_data:
            error_type = error_data['error_type']
            frequency = error_data.get('frequency', 1)

            if frequency > 3:
                knowledge_items.append({
                    'type': 'error_pattern',
                    'content': f"Frequent error pattern: {error_type} ({frequency} occurrences)",
                    'category': 'system',
                    'error_type': error_type,
                    'frequency': frequency,
                    'suggested_fix': error_data.get('suggested_fix'),
                    'importance': 0.9
                })

        return knowledge_items

    async def _extract_risk_knowledge(self, risk_data: Dict) -> List[Dict]:
        """Extract risk-related knowledge"""
        knowledge_items = []

        # Correlation risk
        if 'correlation_matrix' in risk_data:
            high_correlations = []
            for pair, corr in risk_data['correlation_matrix'].items():
                if abs(corr) > 0.8:
                    high_correlations.append((pair, corr))

            if high_correlations:
                knowledge_items.append({
                    'type': 'correlation_risk',
                    'content': f"High correlation risk detected: {len(high_correlations)} pairs",
                    'category': 'risk_insight',
                    'correlations': high_correlations,
                    'risk_level': 'HIGH',
                    'importance': 0.8
                })

        return knowledge_items

    async def _analyze_historical_patterns(self, historical_data: Dict) -> List[Dict]:
        """Analyze historical patterns for prediction"""
        patterns = []

        # Simple pattern analysis
        if 'prices' in historical_data:
            prices = historical_data['prices']
            if len(prices) > 20:
                # Detect uptrend
                if prices[-5:] > prices[-10:-5]:
                    patterns.append({
                        'description': 'Uptrend pattern detected in recent prices',
                        'confidence': 0.7,
                        'horizon': 'short_term',
                        'recommendations': ['Consider buy signals', 'Monitor for continuation']
                    })

        return patterns

    def _calculate_quality_score(self, knowledge_item: Dict) -> float:
        """Calculate comprehensive quality score for knowledge item"""
        score = 0.0

        # Novelty factor
        novelty = self._assess_novelty(knowledge_item)
        score += novelty * self.quality_factors['novelty']

        # Accuracy factor (based on historical data)
        accuracy = self._assess_accuracy(knowledge_item)
        score += accuracy * self.quality_factors['accuracy']

        # Applicability factor
        applicability = self._assess_applicability(knowledge_item)
        score += applicability * self.quality_factors['applicability']

        # Actionability factor
        actionability = self._assess_actionability(knowledge_item)
        score += actionability * self.quality_factors['actionability']

        return min(1.0, max(0.0, score))

    def _assess_novelty(self, knowledge_item: Dict) -> float:
        """Assess novelty of knowledge item"""
        # Check if similar knowledge exists
        content = knowledge_item.get('content', '')

        # Simple novelty check (in production, use semantic similarity)
        recent_knowledge = getattr(self, '_recent_knowledge', [])
        for recent in recent_knowledge:
            similarity = self._simple_similarity(content, recent.get('content', ''))
            if similarity > 0.7:
                return 0.2  # Low novelty if similar exists

        return 0.9  # High novelty for new content

    def _assess_accuracy(self, knowledge_item: Dict) -> float:
        """Assess accuracy based on historical data"""
        # In production, track historical accuracy of similar knowledge
        category = knowledge_item.get('category', 'unknown')
        category_accuracy = {
            'trading_strategy': 0.7,
            'market_pattern': 0.6,
            'risk_insight': 0.8,
            'performance': 0.9,
            'system': 0.85
        }
        return category_accuracy.get(category, 0.5)

    def _assess_applicability(self, knowledge_item: Dict) -> float:
        """Assess current applicability"""
        # Check if knowledge is applicable to current conditions
        import datetime
        extraction_time = knowledge_item.get('extraction_timestamp', '')
        if extraction_time:
            try:
                extraction_dt = datetime.fromisoformat(extraction_time)
                hours_old = (datetime.now() - extraction_dt).total_seconds() / 3600
                if hours_old < 1:
                    return 0.9  # Very recent
                elif hours_old < 24:
                    return 0.7  # Recent
                elif hours_old < 168:  # 1 week
                    return 0.5  # Somewhat recent
                else:
                    return 0.3  # Old
            except:
                pass

        return 0.5

    def _assess_actionability(self, knowledge_item: Dict) -> float:
        """Assess how actionable the knowledge is"""
        # Check for actionable recommendations
        if 'suggested_fix' in knowledge_item or 'recommendations' in knowledge_item:
            return 0.9
        elif 'importance' in knowledge_item and knowledge_item['importance'] > 0.7:
            return 0.7
        else:
            return 0.4

    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def _store_knowledge(self, knowledge_item: Dict) -> None:
        """Store knowledge item in backend"""
        if self.storage:
            try:
                # Store in knowledge base
                if hasattr(self.storage, 'add_trading_knowledge'):
                    await self.storage.add_trading_knowledge(
                        knowledge_type=knowledge_item.get('type'),
                        content=knowledge_item.get('content'),
                        metadata=knowledge_item
                    )

                # Keep track of recent knowledge for novelty assessment
                if not hasattr(self, '_recent_knowledge'):
                    self._recent_knowledge = []
                self._recent_knowledge.append(knowledge_item)

                # Keep only recent knowledge (last 100 items)
                if len(self._recent_knowledge) > 100:
                    self._recent_knowledge = self._recent_knowledge[-100:]

            except Exception as e:
                logger.warning(f"Failed to store knowledge: {e}")

    async def _update_knowledge_graph(self, knowledge_items: List[Dict]) -> None:
        """Update knowledge graph relationships"""
        for item in knowledge_items:
            # Extract concepts from content
            concepts = self._extract_concepts(item.get('content', ''))

            # Update co-occurrence
            for concept in concepts:
                for other_concept in concepts:
                    if concept != other_concept:
                        self.concept_cooccurrence[(concept, other_concept)] += 1

            # Update graph
            if len(concepts) > 1:
                for i, concept1 in enumerate(concepts):
                    for concept2 in concepts[i+1:]:
                        self.knowledge_graph[concept1].add(concept2)
                        self.knowledge_graph[concept2].add(concept1)

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Simple concept extraction
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter out common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
                     'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                     'during', 'before', 'after', 'above', 'below', 'between', 'under',
                     'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
                     'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
                     'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                     'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because',
                     'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
                     'against', 'between', 'into', 'through', 'during', 'before', 'after',
                     'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
                     'off', 'over', 'under', 'again', 'further', 'then', 'once'}

        concepts = [word for word in words if len(word) > 3 and word not in stop_words]

        # Return unique concepts
        return list(set(concepts))

    async def get_intelligent_recommendations(
        self,
        context: str,
        max_recommendations: int = 5
    ) -> List[Dict]:
        """Get intelligent knowledge recommendations based on context

        Args:
            context: Current context or situation
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommended knowledge items with relevance scores
        """
        recommendations = []

        # Extract context concepts
        context_concepts = self._extract_concepts(context)

        # Search knowledge graph for related concepts
        related_concepts = set()
        for concept in context_concepts:
            if concept in self.knowledge_graph:
                related_concepts.update(self.knowledge_graph[concept])

        # Get recent high-quality knowledge
        recent_knowledge = getattr(self, '_recent_knowledge', [])

        # Score knowledge based on concept relevance
        scored_knowledge = []
        for knowledge in recent_knowledge:
            relevance = self._calculate_relevance(knowledge, context_concepts, related_concepts)
            if relevance > 0.3:  # Relevance threshold
                scored_knowledge.append((knowledge, relevance))

        # Sort by relevance and quality
        scored_knowledge.sort(key=lambda x: (x[1], x[0].get('quality_score', 0)), reverse=True)

        # Return top recommendations
        for knowledge, relevance in scored_knowledge[:max_recommendations]:
            recommendations.append({
                'content': knowledge.get('content', ''),
                'category': knowledge.get('category', 'unknown'),
                'quality_score': knowledge.get('quality_score', 0),
                'relevance_score': relevance,
                'importance': knowledge.get('importance', 0),
                'actionable_recommendations': knowledge.get('actionable_recommendations', [])
            })

        return recommendations

    def _calculate_relevance(
        self,
        knowledge: Dict,
        context_concepts: Set[str],
        related_concepts: Set[str]
    ) -> float:
        """Calculate relevance score for knowledge given context"""
        content = knowledge.get('content', '')
        knowledge_concepts = set(self._extract_concepts(content))

        # Direct concept overlap
        direct_overlap = len(context_concepts.intersection(knowledge_concepts))

        # Related concept overlap
        related_overlap = len(related_concepts.intersection(knowledge_concepts))

        # Combine with quality score
        quality = knowledge.get('quality_score', 0.5)

        relevance = (direct_overlap * 0.7 + related_overlap * 0.3) / max(1, len(context_concepts))
        relevance *= quality

        return min(1.0, relevance)

    def get_extraction_statistics(self) -> Dict:
        """Get knowledge extraction statistics"""
        return {
            'total_extractions': self.extraction_stats['total_extractions'],
            'successful_extractions': self.extraction_stats['successful_extractions'],
            'extraction_accuracy': self.extraction_stats['extraction_accuracy'],
            'categories_extracted': dict(self.extraction_stats['categories_extracted']),
            'knowledge_graph_size': len(self.knowledge_graph),
            'concept_cooccurrence_count': len(self.concept_cooccurrence)
        }

    async def start_background_processing(self) -> None:
        """Start background knowledge processing"""
        async with self._processing_lock:
            if not self._processing:
                self._processing = True
                logger.info("Background knowledge processing started")

    async def stop_background_processing(self) -> None:
        """Stop background knowledge processing"""
        async with self._processing_lock:
            self._processing = False
            logger.info("Background knowledge processing stopped")

    def is_processing(self) -> bool:
        """Check if background processing is active"""
        return self._processing