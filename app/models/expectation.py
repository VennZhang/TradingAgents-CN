from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SectorView(BaseModel):
    sector_name: str = Field(..., description="板块名称（申万行业）")
    thesis: str = Field("", description="观点描述")
    confidence: str = Field("中", description="信心度: 高/中/低")
    time_horizon: str = Field("短期", description="时间维度: 短期/中期/长期")


class CustomSection(BaseModel):
    title: str = Field(..., description="自定义章节标题")
    content: str = Field("", description="自定义章节内容")


class ExpectationContent(BaseModel):
    policy_long_term: str = Field("", description="长期政策方向（5年规划级别）")
    policy_medium_term: str = Field("", description="中期宏观政策（最近半年最重要政策）")
    policy_short_term: str = Field("", description="短期政策/事件（最近一月最重要政策）")
    liquidity_assessment: str = Field("", description="流动性判断（未来一月）")
    economic_phase: str = Field("", description="经济周期定位")
    cycle_detail: str = Field("", description="经济周期详细描述")
    market_trend: str = Field("", description="市场大势判断")
    market_phase_detail: str = Field("", description="市场阶段详细描述")
    sector_views: List[SectorView] = Field(default_factory=list, description="板块观点列表")
    custom_sections: List[CustomSection] = Field(default_factory=list, description="自定义补充章节")


class ExpectationCreate(BaseModel):
    title: str = Field(..., description="预期标题")
    content: ExpectationContent = Field(default_factory=ExpectationContent, description="预期内容")


class ExpectationUpdate(BaseModel):
    title: Optional[str] = Field(None, description="预期标题")
    content: Optional[ExpectationContent] = Field(None, description="预期内容")
    is_active: Optional[bool] = Field(None, description="是否为激活预期")


class ExpectationResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    content: ExpectationContent
    is_active: bool = False
    created_at: datetime
    updated_at: datetime
