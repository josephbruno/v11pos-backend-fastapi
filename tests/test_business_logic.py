"""
Unit tests for business logic utilities
"""
import pytest
from app.business_logic import (
    OrderCalculator, LoyaltyCalculator, KOTGrouper, OrderValidator
)
from datetime import datetime, timedelta


class TestOrderCalculator:
    """Test order calculation functions"""
    
    def test_calculate_subtotal(self):
        """Test subtotal calculation"""
        items = [
            {"quantity": 2, "unit_price": 1000},  # $20.00
            {"quantity": 1, "unit_price": 1500},  # $15.00
        ]
        subtotal = OrderCalculator.calculate_subtotal(items)
        assert subtotal == 3500  # $35.00 in cents
    
    def test_calculate_subtotal_empty(self):
        """Test subtotal with empty items"""
        subtotal = OrderCalculator.calculate_subtotal([])
        assert subtotal == 0
    
    def test_calculate_tax(self):
        """Test tax calculation"""
        subtotal = 10000  # $100.00
        tax_percentage = 1050  # 10.50%
        tax = OrderCalculator.calculate_tax(subtotal, tax_percentage)
        assert tax == 1050  # $10.50
    
    def test_calculate_tax_zero(self):
        """Test tax calculation with zero percentage"""
        tax = OrderCalculator.calculate_tax(10000, 0)
        assert tax == 0
    
    def test_calculate_service_charge(self):
        """Test service charge calculation"""
        subtotal = 10000  # $100.00
        service_percentage = 500  # 5.00%
        charge = OrderCalculator.calculate_service_charge(subtotal, service_percentage)
        assert charge == 500  # $5.00
    
    def test_apply_discount_fixed(self):
        """Test fixed discount application"""
        subtotal = 10000
        discount, discount_type = OrderCalculator.apply_discount(subtotal, discount_amount=500)
        assert discount == 500
        assert discount_type == "fixed"
    
    def test_apply_discount_percentage(self):
        """Test percentage discount application"""
        subtotal = 10000  # $100.00
        discount, discount_type = OrderCalculator.apply_discount(subtotal, discount_percentage=1000)  # 10%
        assert discount == 1000  # $10.00
        assert discount_type == "percentage"
    
    def test_calculate_total(self):
        """Test final total calculation"""
        subtotal = 10000
        tax = 1050
        service_charge = 500
        discount = 1000
        tip = 200
        
        total = OrderCalculator.calculate_total(
            subtotal, tax, service_charge, discount, tip
        )
        assert total == 10750
    
    def test_calculate_order_totals_comprehensive(self):
        """Test comprehensive order calculation"""
        items = [
            {"quantity": 2, "unit_price": 1000},
            {"quantity": 1, "unit_price": 1500},
        ]
        
        result = OrderCalculator.calculate_order_totals(
            items=items,
            tax_percentage=1050,  # 10.50%
            service_charge_percentage=500,  # 5%
            discount_amount=100,
            tip=200,
            loyalty_points_redeemed=100,
            loyalty_redemption_rate=0.1
        )
        
        assert result["subtotal"] == 3500
        assert result["tax"] == 368  # Rounded
        assert result["service_charge"] == 175  # Rounded
        assert "total" in result


class TestLoyaltyCalculator:
    """Test loyalty points calculations"""
    
    def test_calculate_points_earned(self):
        """Test loyalty points earning"""
        order_amount = 10000  # $100.00
        points = LoyaltyCalculator.calculate_points_earned(order_amount, earn_rate=100)
        assert points == 100  # 1 point per dollar
    
    def test_calculate_points_earned_with_multiplier(self):
        """Test loyalty points with multiplier"""
        order_amount = 10000
        points = LoyaltyCalculator.calculate_points_earned(
            order_amount, earn_rate=100, customer_multiplier=1.5
        )
        assert points == 150  # 1.5x multiplier
    
    def test_calculate_points_value(self):
        """Test points to currency conversion"""
        points = 100
        value, reason = LoyaltyCalculator.calculate_points_value(
            points, redeem_rate=100, redemption_value_per_point=0.01
        )
        assert value == 100  # $1.00
        assert reason == "loyalty_redemption"
    
    def test_get_loyalty_tier_bronze(self):
        """Test loyalty tier calculation - Bronze"""
        tier = LoyaltyCalculator.get_loyalty_tier(10000)  # $100
        assert tier["name"] == "Bronze"
        assert tier["multiplier"] == 1.0
    
    def test_get_loyalty_tier_silver(self):
        """Test loyalty tier calculation - Silver"""
        tier = LoyaltyCalculator.get_loyalty_tier(50000)  # $500
        assert tier["name"] == "Silver"
        assert tier["multiplier"] == 1.1
    
    def test_get_loyalty_tier_gold(self):
        """Test loyalty tier calculation - Gold"""
        tier = LoyaltyCalculator.get_loyalty_tier(100000)  # $1000
        assert tier["name"] == "Gold"
        assert tier["multiplier"] == 1.25
    
    def test_apply_expiry(self):
        """Test points expiry calculation"""
        now = datetime.now()
        points_list = [
            {"id": "1", "points": 100, "expires_at": now + timedelta(days=10)},
            {"id": "2", "points": 50, "expires_at": now - timedelta(days=1)},
            {"id": "3", "points": 30, "expires_at": None},
        ]
        
        valid_points, expired = LoyaltyCalculator.apply_expiry(points_list, now)
        assert valid_points == 130  # 100 + 30
        assert "2" in expired


class TestKOTGrouper:
    """Test KOT grouping functions"""
    
    def test_group_items_by_department(self):
        """Test grouping items by department"""
        items = [
            {"id": "1", "department": "kitchen", "product": "burger"},
            {"id": "2", "department": "kitchen", "product": "fries"},
            {"id": "3", "department": "bar", "product": "drink"},
        ]
        
        grouped = KOTGrouper.group_items_by_department(items)
        assert "kitchen" in grouped
        assert "bar" in grouped
        assert len(grouped["kitchen"]) == 2
        assert len(grouped["bar"]) == 1
    
    def test_create_kot_groups(self):
        """Test KOT group creation"""
        items = [
            {"id": "1", "department": "kitchen"},
            {"id": "2", "department": "kitchen"},
            {"id": "3", "department": "bar"},
        ]
        
        kot_groups = KOTGrouper.create_kot_groups("order-123", items)
        assert len(kot_groups) == 2
        assert any(g["department"] == "kitchen" for g in kot_groups)
        assert any(g["department"] == "bar" for g in kot_groups)
    
    def test_calculate_estimated_prep_time(self):
        """Test estimated preparation time calculation"""
        items = [
            {"preparation_time": 15},
            {"preparation_time": 20},
            {"preparation_time": 10},
        ]
        
        est_time = KOTGrouper.calculate_estimated_prep_time(items)
        assert est_time == 20  # Maximum time


class TestOrderValidator:
    """Test order validation functions"""
    
    def test_validate_order_items_valid(self):
        """Test valid order items"""
        items = [
            {"quantity": 2, "unit_price": 1000},
            {"quantity": 1, "unit_price": 1500},
        ]
        is_valid, error = OrderValidator.validate_order_items(items)
        assert is_valid is True
        assert error is None
    
    def test_validate_order_items_empty(self):
        """Test validation with empty items"""
        is_valid, error = OrderValidator.validate_order_items([])
        assert is_valid is False
        assert "at least one item" in error
    
    def test_validate_order_items_invalid_quantity(self):
        """Test validation with invalid quantity"""
        items = [{"quantity": 0, "unit_price": 1000}]
        is_valid, error = OrderValidator.validate_order_items(items)
        assert is_valid is False
    
    def test_validate_customer_details_valid(self):
        """Test valid customer details"""
        is_valid, error = OrderValidator.validate_customer_details(
            "John Doe", "dine_in"
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_customer_details_delivery_without_address(self):
        """Test delivery order without address"""
        is_valid, error = OrderValidator.validate_customer_details(
            "John Doe", "delivery"
        )
        assert is_valid is False
        assert "address" in error.lower()
    
    def test_validate_loyalty_redemption_valid(self):
        """Test valid loyalty redemption"""
        is_valid, error = OrderValidator.validate_loyalty_redemption(
            available_points=100,
            points_to_redeem=50,
            min_redeem_points=10
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_loyalty_redemption_insufficient(self):
        """Test loyalty redemption with insufficient points"""
        is_valid, error = OrderValidator.validate_loyalty_redemption(
            available_points=5,
            points_to_redeem=50,
            min_redeem_points=10
        )
        assert is_valid is False
        assert "Insufficient" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
