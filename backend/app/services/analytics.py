import csv
import io
from datetime import datetime, date, timedelta
from typing import List, Tuple
from sqlalchemy import func, and_, not_
from sqlalchemy.orm import Session
from app.models.shipment import Shipment, ShipmentStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    DashboardOut, DashboardToday, TopAgent, 
    AdminDashboardStats, MonthlyStat, RecentDelivery
)

class AnalyticsService:
    def get_dashboard_statistics(self, db: Session) -> DashboardOut:
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        # Today's totals
        total_today = db.query(Shipment).filter(
            Shipment.created_at >= today_start,
            Shipment.created_at <= today_end
        ).count()
        
        completed_today = db.query(Shipment).filter(
            Shipment.created_at >= today_start,
            Shipment.created_at <= today_end,
            Shipment.status == ShipmentStatus.DELIVERED
        ).count()
        
        pending_today = db.query(Shipment).filter(
            Shipment.created_at >= today_start,
            Shipment.created_at <= today_end,
            Shipment.status != ShipmentStatus.DELIVERED
        ).count()
        
        # Delayed deliveries: Active shipments created in the past (before today)
        delayed = db.query(Shipment).filter(
            Shipment.created_at < today_start,
            Shipment.status != ShipmentStatus.DELIVERED
        ).count()
        
        # Average delivery duration in minutes (difference between created_at and otp_verified_at)
        delivered_shipments = db.query(Shipment).filter(
            Shipment.status == ShipmentStatus.DELIVERED,
            Shipment.otp_verified_at != None
        ).all()
        
        total_time_mins = 0.0
        count = len(delivered_shipments)
        for s in delivered_shipments:
            delta = s.otp_verified_at - s.created_at
            total_time_mins += delta.total_seconds() / 60.0
            
        avg_time = round(total_time_mins / count, 1) if count > 0 else 0.0
        
        # Top delivery agents: group by delivery agent, count delivered
        drivers = db.query(User).filter(User.role == UserRole.DeliveryAgent).all()
        top_agents = []
        
        # Dummy ratings mapping
        ratings = [4.95, 4.88, 4.90, 4.85, 4.80, 4.75]
        
        for idx, d in enumerate(drivers):
            completed_count = db.query(Shipment).filter(
                Shipment.delivery_agent_id == d.id,
                Shipment.status == ShipmentStatus.DELIVERED
            ).count()
            
            rating = ratings[idx % len(ratings)]
            top_agents.append(
                TopAgent(
                    agent_id=d.id,
                    name=d.name,
                    completed_count=completed_count,
                    rating=rating
                )
            )
            
        # Sort by completed count descending
        top_agents.sort(key=lambda x: x.completed_count, reverse=True)
        
        # Calculate dummy revenue (e.g. $15 per completed delivery today)
        revenue = completed_today * 15.0
        
        return DashboardOut(
            today_deliveries=DashboardToday(
                total=total_today,
                pending=pending_today,
                completed=completed_today,
                delayed=delayed
            ),
            average_delivery_time_mins=avg_time,
            total_revenue_dummy=revenue,
            top_agents=top_agents[:5]
        )

    def get_admin_dashboard_stats(self, db: Session) -> AdminDashboardStats:
        """
        Calculates all cumulative KPIs, monthly charts statistics, and recent deliveries 
        for the expanded Admin Dashboard.
        """
        total_shipments = db.query(Shipment).count()
        
        pending_shipments = db.query(Shipment).filter(
            Shipment.status != ShipmentStatus.DELIVERED
        ).count()
        
        delivered_shipments = db.query(Shipment).filter(
            Shipment.status == ShipmentStatus.DELIVERED
        ).count()
        
        active_agents = db.query(User).filter(
            User.role == UserRole.DeliveryAgent
        ).count()
        
        # Group monthly statistics in Python to ensure db-agnostic cross-compilations (MySQL + SQLite)
        all_shipments_dates = db.query(Shipment.created_at).all()
        monthly_map = {}
        for (created_at,) in all_shipments_dates:
            month_key = created_at.strftime("%Y-%m")
            monthly_map[month_key] = monthly_map.get(month_key, 0) + 1
            
        monthly_stats = []
        for month_str in sorted(monthly_map.keys()):
            monthly_stats.append(
                MonthlyStat(month=month_str, count=monthly_map[month_str])
            )
            
        # Get last 5 recent completed deliveries
        recent_shipments = db.query(Shipment).filter(
            Shipment.status == ShipmentStatus.DELIVERED
        ).order_by(Shipment.otp_verified_at.desc()).limit(5).all()
        
        recent_deliveries = []
        for s in recent_shipments:
            recent_deliveries.append(
                RecentDelivery(
                    tracking_number=s.tracking_number,
                    receiver_name=s.receiver_name,
                    status=s.status.value,
                    delivered_at=s.otp_verified_at
                )
            )
            
        return AdminDashboardStats(
            total_shipments=total_shipments,
            pending_shipments=pending_shipments,
            delivered_shipments=delivered_shipments,
            active_delivery_agents=active_agents,
            monthly_stats=monthly_stats,
            recent_deliveries=recent_deliveries
        )

    def export_shipments_csv(self, db: Session, start_date: date, end_date: date) -> bytes:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        shipments = db.query(Shipment).filter(
            Shipment.created_at >= start_datetime,
            Shipment.created_at <= end_datetime
        ).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Tracking Number", "Customer ID", "Delivery Agent ID", 
            "Weight (Kg)", "Pickup Address", "Delivery Address", 
            "Receiver Name", "Receiver Phone", "Receiver Email", 
            "Status", "Created At", "Delivered At"
        ])
        
        for s in shipments:
            delivered_at_str = s.otp_verified_at.strftime("%Y-%m-%d %H:%M:%S") if s.otp_verified_at else ""
            writer.writerow([
                s.tracking_number, s.customer_id, s.delivery_agent_id or "",
                s.weight, s.pickup_address, s.delivery_address,
                s.receiver_name, s.receiver_phone, s.receiver_email,
                s.status.value, s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                delivered_at_str
            ])
            
        return output.getvalue().encode("utf-8")

analytics_service = AnalyticsService()
