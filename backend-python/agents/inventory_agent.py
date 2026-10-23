"""Inventory Management Agent - Handles all supply and inventory operations"""

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .base_agent import BaseAgent

try:
    from database import Supply, SupplyCategory, InventoryTransaction, User, SessionLocal
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class InventoryAgent(BaseAgent):
    """Agent specialized in inventory and supply management operations"""
    
    def __init__(self):
        super().__init__("Inventory Management Agent", "inventory_agent")
    
    def get_tools(self) -> List[str]:
        """Return list of inventory management tools"""
        return [
            "create_supply_category",
            "list_supply_categories",
            "create_supply",
            "list_supplies",
            "get_supply_by_id",
            "update_supply_stock",
            "update_supply",
            "delete_supply",
            "get_low_stock_supplies",
            "list_inventory_transactions",
            "get_supply_usage_report"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Return list of inventory management capabilities"""
        return [
            "Medical supply inventory tracking",
            "Stock level monitoring and alerts",
            "Supply category management",
            "Inventory transaction logging",
            "Automated reorder point tracking",
            "Supply usage analytics and reporting"
        ]
    
    # SUPPLY CATEGORY METHODS
    
    def create_supply_category(self, name: str, description: str = None) -> Dict[str, Any]:
        """Create a new supply category."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            category = SupplyCategory(
                name=name,
                description=description
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            result = self.serialize_model(category)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create supply category: {name}",
                response=f"Supply category created successfully with ID: {result['id']}",
                tool_used="create_supply_category"
            )
            
            return {"success": True, "message": "Supply category created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create supply category: {str(e)}"}

    def list_supply_categories(self) -> Dict[str, Any]:
        """List all supply categories - brief information only."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            categories = db.query(SupplyCategory).all()
            
            # Return only essential information for list views
            result = []
            for category in categories:
                brief_info = {
                    "id": str(category.id),
                    "name": category.name,
                    "description": category.description
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query="List all supply categories",
                response=f"Found {len(result)} supply categories",
                tool_used="list_supply_categories"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list supply categories: {str(e)}"}

    # SUPPLY METHODS
    
    def create_supply(self, item_code: str, name: str, category_id: str, unit_of_measure: str,
                     current_stock: int = 0, minimum_stock_level: int = 10, maximum_stock_level: int = 1000,
                     unit_cost: float = None, supplier: str = None, location: str = None,
                     description: str = None, expiry_date: str = None) -> Dict[str, Any]:
        """Create a new supply item."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            supply = Supply(
                item_code=item_code,
                name=name,
                category_id=uuid.UUID(category_id),
                unit_of_measure=unit_of_measure,
                current_stock=current_stock,
                minimum_stock_level=minimum_stock_level,
                maximum_stock_level=maximum_stock_level,
                unit_cost=unit_cost,
                supplier=supplier,
                location=location,
                description=description,
                expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None
            )
            db.add(supply)
            db.commit()
            db.refresh(supply)
            result = self.serialize_model(supply)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Create supply: {item_code} - {name}",
                response=f"Supply created successfully with ID: {result['id']}",
                tool_used="create_supply"
            )
            
            return {"success": True, "message": "Supply created successfully", "data": result}
        except Exception as e:
            return {"success": False, "message": f"Failed to create supply: {str(e)}"}

    def list_supplies(self, low_stock_only: bool = False, category_id: str = None) -> Dict[str, Any]:
        """List supplies with optional filtering."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(Supply)
            
            filters = []
            if low_stock_only:
                query = query.filter(Supply.current_stock <= Supply.minimum_stock_level)
                filters.append("low_stock_only: True")
            if category_id:
                query = query.filter(Supply.category_id == uuid.UUID(category_id))
                filters.append(f"category_id: {category_id}")
            
            supplies = query.all()
            
            # Return only essential information for list views
            result = []
            for supply in supplies:
                brief_info = {
                    "id": str(supply.id),
                    "item_code": supply.item_code,
                    "name": supply.name,
                    "current_stock": supply.current_stock,
                    "minimum_stock_level": supply.minimum_stock_level,
                    "unit_of_measure": supply.unit_of_measure,
                    "category_id": str(supply.category_id) if supply.category_id else None
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            filter_text = f" with filters: {', '.join(filters)}" if filters else ""
            self.log_interaction(
                query=f"List supplies{filter_text}",
                response=f"Found {len(result)} supplies",
                tool_used="list_supplies"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list supplies: {str(e)}"}

    def get_supply_by_id(self, supply_id: str) -> Dict[str, Any]:
        """Get supply by ID."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            supply = db.query(Supply).filter(Supply.id == uuid.UUID(supply_id)).first()
            result = self.serialize_model(supply) if supply else None
            db.close()
            
            if result:
                # Log the interaction
                self.log_interaction(
                    query=f"Get supply by ID: {supply_id}",
                    response=f"Supply found: {result.get('name', 'N/A')} ({result.get('item_code', 'N/A')})",
                    tool_used="get_supply_by_id"
                )
                return {"data": result}
            else:
                return {"error": "Supply not found"}
        except Exception as e:
            return {"error": f"Failed to get supply: {str(e)}"}

    def get_low_stock_supplies(self) -> Dict[str, Any]:
        """Get all supplies that are below minimum stock level."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            supplies = db.query(Supply).filter(Supply.current_stock <= Supply.minimum_stock_level).all()
            result = [self.serialize_model(supply) for supply in supplies]
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query="Get low stock supplies",
                response=f"Found {len(result)} supplies below minimum stock level",
                tool_used="get_low_stock_supplies"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to get low stock supplies: {str(e)}"}

    def update_supply_stock(self, supply_id: str, quantity_change: int, transaction_type: str,
                           performed_by: str = None, user_id: str = None, notes: str = None) -> Dict[str, Any]:
        """Update supply stock levels and log the transaction."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()

            # Lock the supply row before reading current_stock.
            #
            # This is a read-modify-write: without the lock, two concurrent
            # decrements both read the same old_stock, both compute the same
            # new_stock, and the second overwrites the first. One decrement is
            # silently lost and the recorded stock is wrong.
            #
            # FOR UPDATE serialises the pair, so the second request reads the
            # value the first committed. The read below, the arithmetic, the
            # sufficiency check and the write all happen inside one transaction
            # while the lock is held.
            #
            # Note: SQLite silently ignores FOR UPDATE, so this protection only
            # exists on PostgreSQL. The concurrency test is Postgres-only.
            supply = (
                db.query(Supply)
                .filter(Supply.id == uuid.UUID(supply_id))
                .with_for_update()
                .first()
            )

            if not supply:
                db.rollback()
                db.close()
                return {"success": False, "message": "Supply not found"}

            # Read after the lock, never before it.
            old_stock = supply.current_stock
            new_stock = old_stock + quantity_change

            if new_stock < 0:
                db.rollback()
                db.close()
                return {"success": False, "message": f"Insufficient stock. Current: {old_stock}, Requested: {abs(quantity_change)}"}
            
            # Update stock
            supply.current_stock = new_stock
            
            # Create inventory transaction record
            # Use performed_by if provided, otherwise use user_id for backward compatibility
            user_for_transaction = performed_by or user_id
            transaction = InventoryTransaction(
                supply_id=uuid.UUID(supply_id),
                transaction_type=transaction_type,
                quantity=quantity_change,  # Use quantity instead of quantity_change
                performed_by=uuid.UUID(user_for_transaction) if user_for_transaction else None,
                notes=f"{notes or ''} | Stock changed from {old_stock} to {new_stock}".strip(" |")
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(supply)
            db.refresh(transaction)
            
            supply_result = self.serialize_model(supply)
            transaction_result = self.serialize_model(transaction)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update stock for supply {supply_id}: {quantity_change} ({transaction_type})",
                response=f"Stock updated from {old_stock} to {new_stock}",
                tool_used="update_supply_stock"
            )
            
            return {
                "success": True, 
                "message": "Supply stock updated successfully", 
                "data": {
                    "supply": supply_result,
                    "transaction": transaction_result
                }
            }
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Failed to update supply stock: {str(e)}"}

    def update_supply(self, supply_id: str, name: str = None, unit_of_measure: str = None,
                     minimum_stock_level: int = None, maximum_stock_level: int = None,
                     unit_cost: float = None, supplier: str = None) -> Dict[str, Any]:
        """Update supply information."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            supply = db.query(Supply).filter(Supply.id == uuid.UUID(supply_id)).first()
            
            if not supply:
                db.close()
                return {"success": False, "message": "Supply not found"}
            
            # Update provided fields
            update_fields = []
            if name is not None:
                supply.name = name
                update_fields.append("name")
            if unit_of_measure is not None:
                supply.unit_of_measure = unit_of_measure
                update_fields.append("unit_of_measure")
            if minimum_stock_level is not None:
                supply.minimum_stock_level = minimum_stock_level
                update_fields.append("minimum_stock_level")
            if maximum_stock_level is not None:
                supply.maximum_stock_level = maximum_stock_level
                update_fields.append("maximum_stock_level")
            if unit_cost is not None:
                supply.unit_cost = unit_cost
                update_fields.append("unit_cost")
            if supplier is not None:
                supply.supplier = supplier
                update_fields.append("supplier")
            
            db.commit()
            db.refresh(supply)
            result = self.serialize_model(supply)
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Update supply {supply_id}: {', '.join(update_fields)}",
                response=f"Supply updated successfully",
                tool_used="update_supply"
            )
            
            return {"success": True, "message": "Supply updated successfully", "data": result}
        except Exception as e:
            db.rollback()
            db.close()
            return {"success": False, "message": f"Failed to update supply: {str(e)}"}

    def list_inventory_transactions(self, supply_id: str = None, transaction_type: str = None,
                                   start_date: str = None, end_date: str = None, limit: int = 100) -> Dict[str, Any]:
        """List inventory transactions with optional filtering."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            db = self.get_db_session()
            query = db.query(InventoryTransaction)
            
            filters = []
            if supply_id:
                query = query.filter(InventoryTransaction.supply_id == uuid.UUID(supply_id))
                filters.append(f"supply_id: {supply_id}")
            if transaction_type:
                query = query.filter(InventoryTransaction.transaction_type == transaction_type)
                filters.append(f"transaction_type: {transaction_type}")
            if start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(InventoryTransaction.transaction_date >= start_date_obj)
                filters.append(f"start_date: {start_date}")
            if end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(InventoryTransaction.transaction_date <= end_date_obj)
                filters.append(f"end_date: {end_date}")
            
            # Order by most recent first and limit results
            query = query.order_by(InventoryTransaction.transaction_date.desc()).limit(limit)
            
            transactions = query.all()
            
            # Return only essential information for list views
            result = []
            for transaction in transactions:
                brief_info = {
                    "id": str(transaction.id),
                    "supply_id": str(transaction.supply_id) if transaction.supply_id else None,
                    "transaction_type": transaction.transaction_type,
                    "quantity": transaction.quantity,  # Use quantity instead of quantity_change
                    "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                    "performed_by": str(transaction.performed_by) if transaction.performed_by else None,
                    "notes": transaction.notes
                }
                result.append(brief_info)
            
            db.close()
            
            # Log the interaction
            filter_text = f" with filters: {', '.join(filters)}" if filters else ""
            self.log_interaction(
                query=f"List inventory transactions{filter_text} (limit: {limit})",
                response=f"Found {len(result)} transactions",
                tool_used="list_inventory_transactions"
            )
            
            return {"data": result}
        except Exception as e:
            return {"error": f"Failed to list inventory transactions: {str(e)}"}

    def get_supply_usage_report(self, supply_id: str = None, start_date: str = None, 
                               end_date: str = None) -> Dict[str, Any]:
        """Get supply usage report for the specified period."""
        if not DATABASE_AVAILABLE:
            return {"error": "Database not available"}
        
        try:
            from datetime import timedelta
            db = self.get_db_session()
            
            # Calculate date range
            if end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_date_obj = datetime.now()
                
            if start_date:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            else:
                start_date_obj = end_date_obj - timedelta(days=30)  # Default to 30 days
            
            query = db.query(InventoryTransaction).filter(
                InventoryTransaction.transaction_date >= start_date_obj,
                InventoryTransaction.transaction_date <= end_date_obj
            )
            
            if supply_id:
                query = query.filter(InventoryTransaction.supply_id == uuid.UUID(supply_id))
            
            transactions = query.all()
            
            # Process usage statistics
            usage_stats = {}
            for transaction in transactions:
                supply_id_str = str(transaction.supply_id)
                if supply_id_str not in usage_stats:
                    usage_stats[supply_id_str] = {
                        "total_in": 0,
                        "total_out": 0,
                        "net_change": 0,
                        "transaction_count": 0
                    }
                
                stats = usage_stats[supply_id_str]
                stats["transaction_count"] += 1
                
                quantity = transaction.quantity
                if transaction.transaction_type == "in":
                    stats["total_in"] += abs(quantity)
                    stats["net_change"] += abs(quantity)
                elif transaction.transaction_type == "out":
                    stats["total_out"] += abs(quantity)
                    stats["net_change"] -= abs(quantity)
                else:  # adjustment
                    if quantity > 0:
                        stats["total_in"] += quantity
                        stats["net_change"] += quantity
                    else:
                        stats["total_out"] += abs(quantity)
                        stats["net_change"] += quantity  # quantity is already negative for adjustments
            
            result = [self.serialize_model(transaction) for transaction in transactions]
            db.close()
            
            # Log the interaction
            days_diff = (end_date_obj - start_date_obj).days
            self.log_interaction(
                query=f"Get supply usage report for {days_diff} days" + (f" (supply: {supply_id})" if supply_id else ""),
                response=f"Generated usage report with {len(result)} transactions",
                tool_used="get_supply_usage_report"
            )
            
            return {
                "data": result,
                "usage_statistics": usage_stats,
                "period": {
                    "start_date": start_date_obj.isoformat(),
                    "end_date": end_date_obj.isoformat(),
                    "days": days_diff
                }
            }
        except Exception as e:
            return {"error": f"Failed to generate supply usage report: {str(e)}"}

    def delete_supply(self, supply_id: str) -> Dict[str, Any]:
        """Delete a supply item."""
        if not DATABASE_AVAILABLE:
            return {"success": False, "message": "Database not available"}
        
        try:
            db = self.get_db_session()
            supply = db.query(Supply).filter(Supply.id == uuid.UUID(supply_id)).first()
            
            if not supply:
                db.close()
                return {"success": False, "message": "Supply not found"}
            
            supply_name = supply.name  # Store for logging
            db.delete(supply)
            db.commit()
            db.close()
            
            # Log the interaction
            self.log_interaction(
                query=f"Delete supply: {supply_id}",
                response=f"Supply {supply_name} deleted successfully",
                tool_used="delete_supply"
            )
            
            return {"success": True, "message": "Supply deleted successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to delete supply: {str(e)}"}
