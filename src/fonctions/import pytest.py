import pytest
from datetime import datetime
from math import exp, log
from ..fonctions.decroissance import DecroissanceDialog
from PySide6.QtCore import QDate

class TestDecroissanceDialog:
    @pytest.fixture
    def dialog(self):
        """Create a fresh dialog instance for each test"""
        return DecroissanceDialog()

    def test_activity_halves_after_one_period(self, dialog):
        """Test that activity is halved after one period"""
        # Setup
        dialog.period_seconds = 3600  # 1 hour period
        dialog.activity_input.setValue(1000)
        dialog.activity_unit.setCurrentText("Bq")
        
        # Set date to exactly one period ago
        current_time = datetime.now()
        one_period_ago = current_time.replace(hour=current_time.hour - 1)
        test_date = QDate(
            one_period_ago.year,
            one_period_ago.month,
            one_period_ago.day
        )
        dialog.date_input.setDate(test_date)

        # Execute
        dialog.calculate_decay()

        # Assert - should be 500 Bq (half of 1000)
        result_text = dialog.result_bq_label.text()
        result_value = float(result_text.split()[0])
        expected = 500
        assert abs(result_value - expected) < 1  # Allow small floating point difference

    def test_activity_quarters_after_two_periods(self, dialog):
        """Test that activity is reduced to 1/4 after two periods"""
        # Setup
        dialog.period_seconds = 3600  # 1 hour period
        dialog.activity_input.setValue(1000)
        dialog.activity_unit.setCurrentText("Bq")
        
        # Set date to exactly two periods ago
        current_time = datetime.now()
        two_periods_ago = current_time.replace(hour=current_time.hour - 2)
        test_date = QDate(
            two_periods_ago.year,
            two_periods_ago.month,
            two_periods_ago.day
        )
        dialog.date_input.setDate(test_date)

        # Execute
        dialog.calculate_decay()

        # Assert - should be 250 Bq (quarter of 1000)
        result_text = dialog.result_bq_label.text()
        result_value = float(result_text.split()[0])
        expected = 250
        assert abs(result_value - expected) < 1  # Allow small floating point difference

    def test_activity_conversion_units(self, dialog):
        """Test activity conversion between different units"""
        # Setup
        dialog.period_seconds = 3600
        dialog.activity_input.setValue(1)
        dialog.activity_unit.setCurrentText("GBq")
        
        # Set date to exactly one period ago
        current_time = datetime.now()
        one_period_ago = current_time.replace(hour=current_time.hour - 1)
        test_date = QDate(
            one_period_ago.year,
            one_period_ago.month,
            one_period_ago.day
        )
        dialog.date_input.setDate(test_date)

        # Execute
        dialog.calculate_decay()

        # Assert - 1 GBq should decay to 0.5 GBq
        result_text = dialog.result_gbq_label.text()
        result_value = float(result_text.split()[0])
        expected = 0.5
        assert abs(result_value - expected) < 0.01

    def test_invalid_period(self, dialog):
        """Test handling of invalid/zero period"""
        # Setup
        dialog.period_seconds = 0
        dialog.activity_input.setValue(1000)
        dialog.activity_unit.setCurrentText("Bq")

        # Execute & Assert 
        # The calculate_decay method should handle this gracefully
        dialog.calculate_decay()
        # Results should not be updated
        assert dialog.result_bq_label.text() == ""
