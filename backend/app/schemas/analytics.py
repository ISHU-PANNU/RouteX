from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class DashboardToday(BaseModel):
    total: int
    pending: int
    completed: int
    delayed: int

class TopAgent(BaseModel):
    agent_id: int
    name: str
    completed_count: int
    rating: float

class DashboardOut(BaseModel):
    today_deliveries: DashboardToday
    average_delivery_time_mins: float
    total_revenue_dummy: float
    top_agents: List[TopAgent]

class MonthlyStat(BaseModel):
    month: str
    count: int

class RecentDelivery(BaseModel):
    tracking_number: str
    receiver_name: str
    status: str
    delivered_at: Optional[datetime] = None

class AdminDashboardStats(BaseModel):
    total_shipments: int
    pending_shipments: int
    delivered_shipments: int
    active_delivery_agents: int
    monthly_stats: List[MonthlyStat]
    recent_deliveries: List[RecentDelivery]
