"""
ReAct 基类模块
提供ReAct循环的基础实现
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass

from .models import Thought, Reflection, ModuleResult


@dataclass
class Observations:
    """观察结果基类"""
    success: bool = True
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ReActModule(ABC):
    """
    ReAct模块基类
    
    所有功能模块都应继承此类，实现标准的ReAct循环:
    Thought -> Action -> Observe -> Reflect -> (Adapt)
    """
    
    def __init__(self, name: str):
        self.name = name
        self.thought: Optional[Thought] = None
        self.observations: Optional[Observations] = None
        self.reflection: Optional[Reflection] = None
        
    async def execute(self, input_data: Any) -> ModuleResult:
        """
        执行ReAct循环
        
        Args:
            input_data: 输入数据
            
        Returns:
            ModuleResult: 执行结果
        """
        try:
            # Step 1: Thought - 思考
            self.thought = self.think(input_data)
            
            # 保存原始输入到metadata（供后续使用）
            if self.thought.metadata is None:
                self.thought.metadata = {}
            self.thought.metadata['_input_data'] = input_data
            
            # Step 2: Action - 执行
            output = await self.act(self.thought)
            
            # Step 3: Observe - 观察
            self.observations = self.observe(output)
            
            # Step 4: Reflect - 反思
            self.reflection = self.reflect(self.observations)
            
            # Step 5: Adapt - 调整（如果需要）
            if self.reflection.needs_adjustment:
                output = await self.adapt(output, self.reflection)
                # 重新观察和反思
                self.observations = self.observe(output)
                self.reflection = self.reflect(self.observations)
            
            return ModuleResult(
                success=self.reflection.success,
                output=output,
                reflection=self.reflection
            )
            
        except Exception as e:
            import traceback
            return ModuleResult(
                success=False,
                error=f"{self.name}模块执行失败: {str(e)}\n{traceback.format_exc()}"
            )
    
    @abstractmethod
    def think(self, input_data: Any) -> Thought:
        """
        思考阶段
        
        分析输入数据，形成执行策略
        
        Args:
            input_data: 输入数据
            
        Returns:
            Thought: 思考结果
        """
        pass
    
    @abstractmethod
    async def act(self, thought: Thought) -> Any:
        """
        执行阶段
        
        根据思考结果执行具体操作
        
        Args:
            thought: 思考结果
            
        Returns:
            执行输出
        """
        pass
    
    @abstractmethod
    def observe(self, output: Any) -> Observations:
        """
        观察阶段
        
        观察执行结果，提取关键信息
        
        Args:
            output: 执行输出
            
        Returns:
            Observations: 观察结果
        """
        pass
    
    @abstractmethod
    def reflect(self, observations: Observations) -> Reflection:
        """
        反思阶段
        
        根据观察结果进行反思，决定下一步行动
        
        Args:
            observations: 观察结果
            
        Returns:
            Reflection: 反思结果
        """
        pass
    
    async def adapt(self, output: Any, reflection: Reflection) -> Any:
        """
        调整阶段（可选）
        
        根据反思结果调整输出
        
        Args:
            output: 原始输出
            reflection: 反思结果
            
        Returns:
            调整后的输出
        """
        # 默认不调整，子类可覆盖
        return output


class ReActMixin:
    """
    ReAct混入类
    
    为已有类添加ReAct能力
    """
    
    def __init__(self):
        self._thought: Optional[Thought] = None
        self._observations: Optional[Observations] = None
        self._reflection: Optional[Reflection] = None
    
    def _create_thought(self, reasoning: str, confidence: float = 0.8, **kwargs) -> Thought:
        """创建思考结果"""
        return Thought(
            reasoning=reasoning,
            confidence=confidence,
            metadata=kwargs
        )
    
    def _create_reflection(
        self,
        success: bool,
        issues: Optional[list] = None,
        suggestions: Optional[list] = None,
        needs_adjustment: bool = False,
        action: str = "complete"
    ) -> Reflection:
        """创建反思结果"""
        return Reflection(
            success=success,
            issues=issues or [],
            suggestions=suggestions or [],
            needs_adjustment=needs_adjustment,
            action=action
        )
    
    def _combine_reflections(self, *reflections: Reflection) -> Reflection:
        """合并多个反思结果"""
        all_issues = []
        all_suggestions = []
        any_needs_adjustment = False
        min_confidence = 1.0
        
        for r in reflections:
            all_issues.extend(r.issues)
            all_suggestions.extend(r.suggestions)
            any_needs_adjustment = any_needs_adjustment or r.needs_adjustment
            min_confidence = min(min_confidence, r.confidence)
        
        return Reflection(
            success=all(r.success for r in reflections),
            issues=list(set(all_issues)),
            suggestions=list(set(all_suggestions)),
            needs_adjustment=any_needs_adjustment,
            confidence=min_confidence
        )
