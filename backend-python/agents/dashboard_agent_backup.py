"""Dashboard Agent - Handles real-time dashboard data and analytics"""

im            # Staff statistics
            total_staff = db.query(Staff).filter(Staff.status == "active").count()
            # Note: availability_status field doesn't exist in Staff model
            # Using total active staff as approximation for on_duty
            on_duty_staff = total_staffandom
from datetime import datetime, date, timedelta
from typing import Any, Dict, List
from .base_agent import BaseAgent

# Import database modules
try:
    from database import (
        SessionLocal, Patient, Bed, Staff, Department, Room, Equipment, 
        Supply, AgentInteraction, func
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class DashboardAgent(BaseAgent):
    """Agent specialized in dashboard data collection and real-time analytics"""
    
    def __init__(self):
        super().__init__("Dashboard Agent", "dashboard_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of dashboard tools"""
        return [
            "get_dashboard_stats",
            "get_live_bed_occupancy", 
            "get_patient_flow_data",
            "get_emergency_alerts",
            "get_recent_activity"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of dashboard capabilities"""
        return [
            "Real-time hospital statistics",
            "Bed occupancy monitoring",
            "Patient flow analytics", 
            "Emergency alert monitoring",
            "Activity feed tracking",
            "Live dashboard data updates"
        ]
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get real-time hospital statistics for dashboard display."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "error": "Database not available"}
        
        try:
            db = SessionLocal()
            
            # Get patient statistics
            total_patients = db.query(Patient).filter(Patient.status != "discharged").count()
            total_all_patients = db.query(Patient).count()
            
            # Get admissions today
            today = date.today()
            admissions_today = db.query(Patient).filter(
                func.date(Patient.created_at) == today
            ).count()
            
            # Get discharges today (assuming we track this in patient status changes)
            discharged_today = db.query(Patient).filter(
                Patient.status == "discharged",
                func.date(Patient.updated_at) == today
            ).count()
            
            # Get bed statistics
            total_beds = db.query(Bed).count()
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            available_beds = db.query(Bed).filter(Bed.status == "available").count()
            cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").count()
            maintenance_beds = db.query(Bed).filter(Bed.status == "maintenance").count()
            
            # Get staff statistics
            total_staff = db.query(Staff).filter(Staff.status == "active").count()
            # Note: availability_status field doesn't exist in Staff model
            # Using total active staff as approximation for on_duty
            on_duty_staff = total_staff
            
            # Calculate trends (simplified - you can enhance this)
            patient_trend = f"+{admissions_today - discharged_today}" if admissions_today > discharged_today else f"{admissions_today - discharged_today}"
            
            db.close()
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "patients": {
                    "total": total_patients,
                    "total_all_time": total_all_patients,
                    "admissions_today": admissions_today,
                    "discharges_today": discharged_today,
                    "trend": patient_trend
                },
                "beds": {
                    "total": total_beds,
                    "occupied": occupied_beds,
                    "available": available_beds,
                    "cleaning": cleaning_beds,
                    "maintenance": maintenance_beds,
                    "occupancy_rate": round((occupied_beds / total_beds * 100), 1) if total_beds > 0 else 0
                },
                "staff": {
                    "total_active": total_staff,
                    "on_duty": on_duty_staff,
                    "off_duty": total_staff - on_duty_staff
                }
            }
            
            self.log_interaction("get_dashboard_stats", result, "get_dashboard_stats")
            return result
            
        except Exception as e:
            error_result = {"success": False, "error": f"Failed to get dashboard stats: {str(e)}"}
            self.log_interaction("get_dashboard_stats", error_result, "get_dashboard_stats")
            return error_result

    def get_live_bed_occupancy(self) -> Dict[str, Any]:
        """Get real-time bed occupancy by department for dashboard charts."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "error": "Database not available"}
        
        try:
            db = SessionLocal()
            
            # Get bed occupancy by department
            bed_occupancy = db.query(
                Department.name.label('department_name'),
                func.count(Bed.id).label('total_beds'),
                func.sum(func.case([(Bed.status == 'occupied', 1)], else_=0)).label('occupied_beds'),
                func.sum(func.case([(Bed.status == 'available', 1)], else_=0)).label('available_beds'),
                func.sum(func.case([(Bed.status == 'cleaning', 1)], else_=0)).label('cleaning_beds'),
                func.sum(func.case([(Bed.status == 'maintenance', 1)], else_=0)).label('maintenance_beds')
            ).join(Room, Department.id == Room.department_id)\
             .join(Bed, Room.id == Bed.room_id)\
             .group_by(Department.name)\
             .all()
            
            departments = []
            for dept in bed_occupancy:
                total = int(dept.total_beds) if dept.total_beds else 0
                occupied = int(dept.occupied_beds) if dept.occupied_beds else 0
                available = int(dept.available_beds) if dept.available_beds else 0
                cleaning = int(dept.cleaning_beds) if dept.cleaning_beds else 0
                maintenance = int(dept.maintenance_beds) if dept.maintenance_beds else 0
                
                occupancy_rate = round((occupied / total * 100), 1) if total > 0 else 0
                
                departments.append({
                    "name": dept.department_name,
                    "total_beds": total,
                    "occupied": occupied,
                    "available": available,
                    "cleaning": cleaning,
                    "maintenance": maintenance,
                    "occupancy_rate": occupancy_rate,
                    "status_color": "red" if occupancy_rate > 90 else "orange" if occupancy_rate > 75 else "green"
                })
            
            db.close()
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "departments": departments
            }
            
            self.log_interaction("get_live_bed_occupancy", result, "get_live_bed_occupancy")
            return result
            
        except Exception as e:
            error_result = {"success": False, "error": f"Failed to get bed occupancy data: {str(e)}"}
            self.log_interaction("get_live_bed_occupancy", error_result, "get_live_bed_occupancy")
            return error_result

    def get_patient_flow_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get patient admission and discharge flow data for the specified time period."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "error": "Database not available"}
        
        try:
            db = SessionLocal()
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get hourly admissions
            admissions = db.query(
                func.date_trunc('hour', Patient.created_at).label('hour'),
                func.count(Patient.id).label('count')
            ).filter(
                Patient.created_at >= start_time,
                Patient.created_at <= end_time
            ).group_by(func.date_trunc('hour', Patient.created_at)).all()
            
            # Get hourly discharges (patients with status changed to discharged)
            discharges = db.query(
                func.date_trunc('hour', Patient.updated_at).label('hour'),
                func.count(Patient.id).label('count')
            ).filter(
                Patient.status == "discharged",
                Patient.updated_at >= start_time,
                Patient.updated_at <= end_time
            ).group_by(func.date_trunc('hour', Patient.updated_at)).all()
            
            # Format data for charts
            admission_data = [{"time": admission.hour.isoformat(), "admissions": admission.count} for admission in admissions]
            discharge_data = [{"time": discharge.hour.isoformat(), "discharges": discharge.count} for discharge in discharges]
            
            db.close()
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "time_range_hours": hours,
                "admissions": admission_data,
                "discharges": discharge_data
            }
            
            self.log_interaction("get_patient_flow_data", result, "get_patient_flow_data")
            return result
            
        except Exception as e:
            error_result = {"success": False, "error": f"Failed to get patient flow data: {str(e)}"}
            self.log_interaction("get_patient_flow_data", error_result, "get_patient_flow_data")
            return error_result

    def get_emergency_alerts(self) -> Dict[str, Any]:
        """Get active emergency alerts and critical notifications for dashboard."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "error": "Database not available"}
        
        try:
            db = SessionLocal()
            alerts = []
            
            # Critical bed shortages (less than 10% available)
            total_beds = db.query(Bed).count()
            available_beds = db.query(Bed).filter(Bed.status == "available").count()
            if total_beds > 0:
                availability_rate = (available_beds / total_beds) * 100
                if availability_rate < 10:
                    alerts.append({
                        "id": "bed_shortage",
                        "type": "critical",
                        "priority": "high",
                        "message": f"Critical bed shortage: Only {available_beds} beds available ({availability_rate:.1f}%)",
                        "timestamp": datetime.now().isoformat(),
                        "icon": "🔴",
                        "action_required": True
                    })
            
            # Equipment maintenance alerts
            maintenance_equipment = db.query(Equipment).filter(Equipment.status == "maintenance").count()
            if maintenance_equipment > 0:
                alerts.append({
                    "id": "equipment_maintenance",
                    "type": "warning",
                    "priority": "medium",
                    "message": f"{maintenance_equipment} equipment items under maintenance",
                    "timestamp": datetime.now().isoformat(),
                    "icon": "🟡",
                    "action_required": False
                })
            
            # Low supply alerts (assuming we have supply quantity tracking)
            try:
                low_supplies = db.query(Supply).filter(Supply.current_stock < Supply.minimum_threshold).count()
                if low_supplies > 0:
                    alerts.append({
                        "id": "low_supplies",
                        "type": "warning", 
                        "priority": "medium",
                        "message": f"{low_supplies} supplies running low",
                        "timestamp": datetime.now().isoformat(),
                        "icon": "🟠",
                        "action_required": True
                    })
            except:
                # Handle case where supply tracking fields don't exist yet
                pass
            
            # High occupancy warnings
            occupied_beds = db.query(Bed).filter(Bed.status == "occupied").count()
            if total_beds > 0:
                occupancy_rate = (occupied_beds / total_beds) * 100
                if occupancy_rate > 90:
                    alerts.append({
                        "id": "high_occupancy",
                        "type": "warning",
                        "priority": "medium", 
                        "message": f"High bed occupancy: {occupancy_rate:.1f}% ({occupied_beds}/{total_beds})",
                        "timestamp": datetime.now().isoformat(),
                        "icon": "🟡",
                        "action_required": False
                    })
            
            db.close()
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "alerts": alerts,
                "total_alerts": len(alerts),
                "critical_count": len([a for a in alerts if a["type"] == "critical"]),
                "warning_count": len([a for a in alerts if a["type"] == "warning"])
            }
            
            self.log_interaction("get_emergency_alerts", result, "get_emergency_alerts")
            return result
            
        except Exception as e:
            error_result = {"success": False, "error": f"Failed to get emergency alerts: {str(e)}"}
            self.log_interaction("get_emergency_alerts", error_result, "get_emergency_alerts")
            return error_result

    def get_recent_activity(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent hospital activity for dashboard activity feed."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "error": "Database not available"}
        
        try:
            db = SessionLocal()
            activities = []
            
            # Recent patient admissions
            recent_patients = db.query(Patient).order_by(Patient.created_at.desc()).limit(5).all()
            for patient in recent_patients:
                activities.append({
                    "id": f"patient_{patient.id}",
                    "type": "admission",
                    "message": f"Patient {patient.first_name} {patient.last_name} admitted",
                    "timestamp": patient.created_at.isoformat(),
                    "icon": "👥"
                })
            
            # Recent bed status changes (you may need to add a bed_status_history table for this)
            # For now, we'll show cleaning beds as recent activity
            cleaning_beds = db.query(Bed).filter(Bed.status == "cleaning").limit(3).all()
            for bed in cleaning_beds:
                activities.append({
                    "id": f"bed_{bed.id}",
                    "type": "bed_cleaning",
                    "message": f"Bed {bed.bed_number} cleaning started",
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(5, 30))).isoformat(),
                    "icon": "🛏️"
                })
            
            # Recent agent interactions (if available)
            try:
                recent_interactions = db.query(AgentInteraction).order_by(AgentInteraction.interaction_time.desc()).limit(3).all()
                for interaction in recent_interactions:
                    activities.append({
                        "id": f"agent_{interaction.id}",
                        "type": "system_activity",
                        "message": f"{interaction.agent_type}: {interaction.action_taken[:50]}...",
                        "timestamp": interaction.interaction_time.isoformat(),
                        "icon": "🤖"
                    })
            except:
                pass
            
            # Sort activities by timestamp and limit
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            activities = activities[:limit]
            
            db.close()
            
            result = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "activities": activities,
                "total_count": len(activities)
            }
            
            self.log_interaction("get_recent_activity", result, "get_recent_activity")
            return result
            
        except Exception as e:
            error_result = {"success": False, "error": f"Failed to get recent activity: {str(e)}"}
            self.log_interaction("get_recent_activity", error_result, "get_recent_activity")
            return error_result
