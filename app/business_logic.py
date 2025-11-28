"""
Business logic utilities for order calculations, loyalty, and KOT management
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


class OrderCalculator:
    """Handles order calculations including tax, discounts, and loyalty points"""
    
    @staticmethod
    def calculate_subtotal(items: List[Dict]) -> int:
        """
        Calculate order subtotal from items
        
        Args:
            items: List of order items with quantity and unit_price
        
        Returns:
            Subtotal in cents
        """
        subtotal = 0
        for item in items:
            subtotal += item.get('quantity', 0) * item.get('unit_price', 0)
        return subtotal
    
    @staticmethod
    def calculate_tax(subtotal: int, tax_percentage: int, applicable_on: str = "all") -> int:
        """
        Calculate tax for order
        
        Args:
            subtotal: Order subtotal in cents
            tax_percentage: Tax percentage (stored as percentage * 100, e.g., 1050 = 10.50%)
            applicable_on: What the tax applies to (all, dine_in, takeaway, delivery)
        
        Returns:
            Tax amount in cents
        """
        if tax_percentage <= 0:
            return 0
        
        # Convert from basis points to actual percentage
        percentage = tax_percentage / 100
        return int(subtotal * percentage / 100)
    
    @staticmethod
    def calculate_service_charge(
        subtotal: int,
        service_charge_percentage: int
    ) -> int:
        """
        Calculate service charge
        
        Args:
            subtotal: Order subtotal in cents
            service_charge_percentage: Service charge percentage (basis points)
        
        Returns:
            Service charge amount in cents
        """
        if service_charge_percentage <= 0:
            return 0
        
        percentage = service_charge_percentage / 100
        return int(subtotal * percentage / 100)
    
    @staticmethod
    def apply_discount(
        subtotal: int,
        discount_amount: int = 0,
        discount_percentage: int = 0
    ) -> Tuple[int, str]:
        """
        Apply discount to subtotal
        
        Args:
            subtotal: Order subtotal in cents
            discount_amount: Fixed discount amount in cents
            discount_percentage: Discount percentage (basis points)
        
        Returns:
            Tuple of (discount_amount, discount_type)
        """
        if discount_percentage > 0:
            percentage = discount_percentage / 100
            return int(subtotal * percentage / 100), "percentage"
        
        if discount_amount > 0:
            # Ensure discount doesn't exceed subtotal
            return min(discount_amount, subtotal), "fixed"
        
        return 0, "none"
    
    @staticmethod
    def calculate_total(
        subtotal: int,
        tax: int,
        service_charge: int,
        discount: int,
        tip: int = 0
    ) -> int:
        """
        Calculate final order total
        
        Args:
            subtotal: Order subtotal
            tax: Tax amount
            service_charge: Service charge amount
            discount: Discount amount
            tip: Tip amount
        
        Returns:
            Final total in cents
        """
        total = subtotal + tax + service_charge - discount + tip
        return max(total, 0)  # Ensure total is never negative
    
    @staticmethod
    def calculate_order_totals(
        items: List[Dict],
        tax_percentage: int = 0,
        service_charge_percentage: int = 0,
        discount_amount: int = 0,
        tip: int = 0,
        loyalty_points_redeemed: int = 0,
        loyalty_redemption_rate: float = 1.0
    ) -> Dict:
        """
        Calculate all order totals comprehensively
        
        Args:
            items: Order items
            tax_percentage: Tax rate in basis points
            service_charge_percentage: Service charge in basis points
            discount_amount: Fixed discount
            tip: Tip amount
            loyalty_points_redeemed: Points to redeem
            loyalty_redemption_rate: Points to currency conversion rate
        
        Returns:
            Dictionary with all calculations
        """
        subtotal = OrderCalculator.calculate_subtotal(items)
        tax = OrderCalculator.calculate_tax(subtotal, tax_percentage)
        service_charge = OrderCalculator.calculate_service_charge(
            subtotal, service_charge_percentage
        )
        discount_amount = min(discount_amount, subtotal)
        
        # Apply loyalty redemption
        loyalty_value = int(loyalty_points_redeemed * loyalty_redemption_rate)
        effective_discount = discount_amount + loyalty_value
        
        total = OrderCalculator.calculate_total(
            subtotal,
            tax,
            service_charge,
            effective_discount,
            tip
        )
        
        return {
            "subtotal": subtotal,
            "tax": tax,
            "service_charge": service_charge,
            "discount": effective_discount,
            "tip": tip,
            "total": total,
            "loyalty_value_redeemed": loyalty_value
        }


class LoyaltyCalculator:
    """Handles loyalty points calculations"""
    
    @staticmethod
    def calculate_points_earned(
        order_amount: int,
        earn_rate: int = 100,
        customer_multiplier: float = 1.0
    ) -> int:
        """
        Calculate loyalty points earned from an order
        
        Args:
            order_amount: Order amount in cents
            earn_rate: Points earning rate (basis points, e.g., 100 = 1.00 points per dollar)
            customer_multiplier: Multiplier for VIP/special customers
        
        Returns:
            Points earned
        """
        # Convert amount from cents to dollars
        amount_in_dollars = order_amount / 100
        
        # Calculate points (earn_rate is in basis points)
        rate = earn_rate / 100
        points = int(amount_in_dollars * rate * customer_multiplier)
        
        return points
    
    @staticmethod
    def calculate_points_value(
        points: int,
        redeem_rate: int = 100,
        redemption_value_per_point: float = 0.01
    ) -> Tuple[int, str]:
        """
        Calculate monetary value of loyalty points
        
        Args:
            points: Number of points
            redeem_rate: Redemption rate (basis points)
            redemption_value_per_point: Value per point in dollars
        
        Returns:
            Tuple of (value_in_cents, reason)
        """
        rate = redeem_rate / 100
        value_in_dollars = points * redemption_value_per_point * (rate / 100)
        value_in_cents = int(value_in_dollars * 100)
        
        return value_in_cents, "loyalty_redemption"
    
    @staticmethod
    def apply_expiry(
        points: List[Dict],
        current_date: datetime = None
    ) -> Tuple[int, List[str]]:
        """
        Calculate points after expiry
        
        Args:
            points: List of point transactions with expiry dates
            current_date: Current date for comparison
        
        Returns:
            Tuple of (remaining_points, expired_transactions)
        """
        if current_date is None:
            current_date = datetime.now()
        
        total_valid_points = 0
        expired = []
        
        for pt in points:
            if pt.get('expires_at') and pt['expires_at'] < current_date:
                expired.append(pt['id'])
            else:
                total_valid_points += pt.get('points', 0)
        
        return total_valid_points, expired
    
    @staticmethod
    def get_loyalty_tier(total_spent: int) -> Dict:
        """
        Determine customer loyalty tier based on total spending
        
        Args:
            total_spent: Total amount spent in cents
        
        Returns:
            Tier information dictionary
        """
        # Tier thresholds (in dollars)
        TIERS = [
            {"name": "Bronze", "threshold": 0, "multiplier": 1.0, "benefits": []},
            {"name": "Silver", "threshold": 50000, "multiplier": 1.1, "benefits": ["5% discount", "Free delivery"]},
            {"name": "Gold", "threshold": 100000, "multiplier": 1.25, "benefits": ["10% discount", "Priority service"]},
            {"name": "Platinum", "threshold": 250000, "multiplier": 1.5, "benefits": ["15% discount", "VIP support"]},
        ]
        
        total_in_dollars = total_spent / 100
        
        # Find appropriate tier
        current_tier = TIERS[0]
        for tier in reversed(TIERS):
            if total_in_dollars >= tier["threshold"] / 100:
                current_tier = tier
                break
        
        return current_tier


class KOTGrouper:
    """Handles KOT (Kitchen Order Ticket) grouping and management"""
    
    @staticmethod
    def group_items_by_department(items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group order items by department
        
        Args:
            items: List of order items
        
        Returns:
            Dictionary with department as key and items list as value
        """
        grouped = defaultdict(list)
        
        for item in items:
            department = item.get('department', 'kitchen').lower()
            grouped[department].append(item)
        
        return dict(grouped)
    
    @staticmethod
    def create_kot_groups(
        order_id: str,
        items: List[Dict]
    ) -> List[Dict]:
        """
        Create KOT groups from order items
        
        Args:
            order_id: Order ID
            items: Order items
        
        Returns:
            List of KOT group dictionaries
        """
        grouped_items = KOTGrouper.group_items_by_department(items)
        
        kot_groups = []
        for department, dept_items in grouped_items.items():
            kot_group = {
                "order_id": order_id,
                "department": department,
                "item_count": len(dept_items),
                "items": dept_items,
                "status": "pending"
            }
            kot_groups.append(kot_group)
        
        return kot_groups
    
    @staticmethod
    def calculate_estimated_prep_time(items: List[Dict]) -> int:
        """
        Calculate estimated preparation time based on items
        
        Args:
            items: Order items with preparation_time field
        
        Returns:
            Estimated time in minutes
        """
        if not items:
            return 15
        
        # Use the maximum preparation time among items
        max_time = max(item.get('preparation_time', 15) for item in items)
        
        return max_time


class OrderValidator:
    """Validates order data and business rules"""
    
    @staticmethod
    def validate_order_items(items: List[Dict]) -> Tuple[bool, Optional[str]]:
        """
        Validate order items
        
        Args:
            items: Order items to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not items:
            return False, "Order must have at least one item"
        
        for item in items:
            if item.get('quantity', 0) <= 0:
                return False, "Item quantity must be greater than 0"
            
            if item.get('unit_price', 0) < 0:
                return False, "Item price cannot be negative"
        
        return True, None
    
    @staticmethod
    def validate_customer_details(
        customer_name: str,
        order_type: str,
        delivery_address: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate customer details for order
        
        Args:
            customer_name: Customer name
            order_type: Type of order (dine_in, takeaway, delivery, qr_order)
            delivery_address: Delivery address if applicable
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not customer_name or not customer_name.strip():
            return False, "Customer name is required"
        
        if order_type == "delivery" and not delivery_address:
            return False, "Delivery address is required for delivery orders"
        
        return True, None
    
    @staticmethod
    def validate_loyalty_redemption(
        available_points: int,
        points_to_redeem: int,
        min_redeem_points: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate loyalty points redemption
        
        Args:
            available_points: Points available to customer
            points_to_redeem: Points they want to redeem
            min_redeem_points: Minimum points required for redemption
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if points_to_redeem <= 0:
            return True, None  # No redemption is valid
        
        if points_to_redeem < min_redeem_points:
            return False, f"Minimum {min_redeem_points} points required for redemption"
        
        if points_to_redeem > available_points:
            return False, "Insufficient loyalty points"
        
        return True, None
