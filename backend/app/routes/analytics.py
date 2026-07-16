from datetime import date
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from app.dependencies.db import get_db
from app.dependencies.auth import RoleChecker
from app.models.user import User, UserRole
from app.schemas.analytics import DashboardOut, AdminDashboardStats
from app.services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["Operational Analytics"])

@router.get(
    "/dashboard", 
    response_model=DashboardOut,
    status_code=status.HTTP_200_OK,
    summary="Fetch Dashboard Statistics",
    description="Calculates counts for active shipments, revenues and agent ratings lists."
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin]))
):
    return analytics_service.get_dashboard_statistics(db)

@router.get(
    "/admin/cumulative", 
    response_model=AdminDashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Get Cumulative Admin Dashboard Statistics",
    description="Returns total, pending, and delivered counts, active agent counts, monthly stats, and recent deliveries."
)
def get_admin_dashboard_cumulative(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin]))
):
    return analytics_service.get_admin_dashboard_stats(db)

@router.get(
    "/reports/export", 
    status_code=status.HTTP_200_OK,
    summary="Export Shipments CSV",
    description="Generates a downloadable CSV document containing shipments logged within the date ranges."
)
def export_csv(
    start_date: date = Query(..., description="Start date bounds (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date bounds (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin]))
):
    csv_bytes = analytics_service.export_shipments_csv(db, start_date=start_date, end_date=end_date)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=shipments_report_{start_date}_to_{end_date}.csv"}
    )
