"""Comprehensive unit tests for computations module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lxml import etree as ET
from io import BytesIO

from ct600.computations import Definition, Computations, CT_NS, CORE_NS
from ixbrl_parse.ixbrl import Period, Instant, Entity, Dimension
# from ixbrl_parse.value import Value  # Not needed for our tests


class TestDefinition:
    """Test the Definition class functionality."""
    
    def test_definition_initialization(self):
        """Test Definition initialization with box and description."""
        definition = Definition(100, "Test description")
        assert definition.box == 100
        assert definition.description == "Test description"
        assert definition.value is None
    
    def test_definition_set_method(self):
        """Test Definition set method returns self and sets value."""
        definition = Definition(100, "Test description")
        result = definition.set("test_value")
        
        # Should return self for chaining
        assert result is definition
        assert definition.value == "test_value"
    
    def test_definition_set_chaining(self):
        """Test Definition set method allows chaining."""
        definition = Definition(100, "Test").set("value1").set("value2")
        assert definition.value == "value2"


class TestComputations:
    """Test the Computations class functionality."""
    
    @pytest.fixture
    def mock_ixbrl_data(self):
        """Create mock IXBRL data for testing."""
        return b"""<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml"
              xmlns:ct="http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01"
              xmlns:core="http://xbrl.frc.org.uk/fr/2023-01-01/core">
            <body>
                <div>Test IXBRL content</div>
            </body>
        </html>"""
    
    @pytest.fixture
    def mock_computations(self, mock_ixbrl_data):
        """Create a Computations instance with mocked dependencies."""
        with patch('ct600.computations.ET.parse') as mock_parse, \
             patch('ct600.computations.ixbrl_parse.ixbrl.parse') as mock_ixbrl_parse:
            
            # Mock the XML tree
            mock_tree = Mock()
            mock_parse.return_value = mock_tree
            
            # Mock the IXBRL object
            mock_ixbrl = Mock()
            mock_ixbrl_parse.return_value = mock_ixbrl
            
            comp = Computations(mock_ixbrl_data)
            comp.ixbrl = mock_ixbrl
            
            return comp
    
    def test_computations_initialization(self, mock_ixbrl_data):
        """Test Computations initialization."""
        with patch('ct600.computations.ET.parse') as mock_parse, \
             patch('ct600.computations.ixbrl_parse.ixbrl.parse') as mock_ixbrl_parse:
            
            mock_tree = Mock()
            mock_parse.return_value = mock_tree
            
            mock_ixbrl = Mock()
            mock_ixbrl_parse.return_value = mock_ixbrl
            
            comp = Computations(mock_ixbrl_data)
            
            # Verify ET.parse was called with BytesIO
            mock_parse.assert_called_once()
            args = mock_parse.call_args[0]
            assert isinstance(args[0], BytesIO)
            
            # Verify IXBRL parse was called
            mock_ixbrl_parse.assert_called_once_with(mock_tree)
            
            assert comp.ixbrl == mock_ixbrl
    
    def test_get_context_success(self, mock_computations):
        """Test get_context method with existing relation."""
        mock_context = Mock()
        mock_context.children = {"test_rel": "child_context"}
        
        result = mock_computations.get_context(mock_context, "test_rel")
        assert result == "child_context"
    
    def test_get_context_missing_relation(self, mock_computations):
        """Test get_context method with missing relation."""
        mock_context = Mock()
        mock_context.children = {}
        
        with pytest.raises(RuntimeError, match="No context test_rel"):
            mock_computations.get_context(mock_context, "test_rel")
    
    def test_value_method(self, mock_computations):
        """Test value method extracts value correctly."""
        mock_value_obj = Mock()
        mock_to_value = Mock()
        mock_to_value.get_value.return_value = "extracted_value"
        mock_value_obj.to_value.return_value = mock_to_value
        
        result = mock_computations.value(mock_value_obj)
        
        assert result == "extracted_value"
        mock_value_obj.to_value.assert_called_once()
        mock_to_value.get_value.assert_called_once()
    
    def test_period_context_success(self, mock_computations):
        """Test period_context method finds latest period."""
        # Mock context iterator with multiple periods
        from datetime import datetime
        
        period1 = Mock(spec=Period)
        period1.end = datetime(2023, 6, 30)
        context1 = Mock()
        
        period2 = Mock(spec=Period)
        period2.end = datetime(2023, 12, 31)
        context2 = Mock()
        
        non_period = Mock()  # Not a Period instance
        context3 = Mock()
        
        mock_computations.ixbrl.context_iter.return_value = [
            (period1, context1, 0),
            (period2, context2, 0),
            (non_period, context3, 0)
        ]
        
        result = mock_computations.period_context()
        
        # Should return the context with the latest end date
        assert result == context2
    
    def test_period_context_no_periods(self, mock_computations):
        """Test period_context method with no period contexts."""
        mock_computations.ixbrl.context_iter.return_value = [
            (Mock(), Mock(), 0),  # Not a Period instance
        ]
        
        with pytest.raises(RuntimeError, match="Expected to find a period context"):
            mock_computations.period_context()
    
    def test_instant_context_success(self, mock_computations):
        """Test instant_context method finds latest instant."""
        from datetime import datetime
        
        instant1 = Mock(spec=Instant)
        instant1.instant = datetime(2023, 6, 30)
        context1 = Mock()
        
        instant2 = Mock(spec=Instant)
        instant2.instant = datetime(2023, 12, 31)
        context2 = Mock()
        
        mock_computations.ixbrl.context_iter.return_value = [
            (instant1, context1, 0),
            (instant2, context2, 0),
        ]
        
        result = mock_computations.instant_context()
        
        # Should return the context with the latest instant
        assert result == context2
    
    def test_instant_context_no_instants(self, mock_computations):
        """Test instant_context method with no instant contexts."""
        mock_computations.ixbrl.context_iter.return_value = [
            (Mock(), Mock(), 0),  # Not an Instant instance
        ]
        
        with pytest.raises(RuntimeError, match="Expected to find an instant context"):
            mock_computations.instant_context()
    
    def test_entity_context_success(self, mock_computations):
        """Test entity_context method finds entity."""
        entity = Mock(spec=Entity)
        context = Mock()
        
        mock_computations.ixbrl.context_iter.return_value = [
            (entity, context, 0),
            (Mock(), Mock(), 0),  # Not an Entity
        ]
        
        result = mock_computations.entity_context()
        assert result == context
    
    def test_entity_context_no_entity(self, mock_computations):
        """Test entity_context method with no entity contexts."""
        mock_computations.ixbrl.context_iter.return_value = [
            (Mock(), Mock(), 0),  # Not an Entity instance
        ]
        
        with pytest.raises(RuntimeError, match="Expected to find an entity context"):
            mock_computations.entity_context()
    
    def test_company_instant_context(self, mock_computations):
        """Test company_instant_context method."""
        mock_instant_context = Mock()
        mock_company_context = Mock()
        
        with patch.object(mock_computations, 'instant_context', return_value=mock_instant_context), \
             patch.object(mock_computations, 'get_context', return_value=mock_company_context) as mock_get_context:
            
            result = mock_computations.company_instant_context()
            
            assert result == mock_company_context
            
            # Verify get_context was called with correct dimension
            mock_get_context.assert_called_once()
            args = mock_get_context.call_args[0]
            assert args[0] == mock_instant_context
            dimension = args[1]
            assert isinstance(dimension, Dimension)
            assert str(dimension.dimension) == str(ET.QName(CT_NS, "BusinessTypeDimension"))
            assert str(dimension.value) == str(ET.QName(CT_NS, "Company"))
    
    def test_company_period_context(self, mock_computations):
        """Test company_period_context method."""
        mock_period_context = Mock()
        mock_company_context = Mock()
        
        with patch.object(mock_computations, 'period_context', return_value=mock_period_context), \
             patch.object(mock_computations, 'get_context', return_value=mock_company_context) as mock_get_context:
            
            result = mock_computations.company_period_context()
            
            assert result == mock_company_context
            mock_get_context.assert_called_once_with(
                mock_period_context,
                Dimension(
                    ET.QName(CT_NS, "BusinessTypeDimension"),
                    ET.QName(CT_NS, "Company")
                )
            )
    
    def test_trade_period_context(self, mock_computations):
        """Test trade_period_context method with multiple dimensions."""
        mock_period_context = Mock()
        mock_trade_context = Mock()
        mock_loss_reform_context = Mock() 
        mock_territory_context = Mock()
        
        with patch.object(mock_computations, 'period_context', return_value=mock_period_context), \
             patch.object(mock_computations, 'get_context') as mock_get_context:
            
            # Set up the chain of get_context calls
            mock_get_context.side_effect = [
                mock_trade_context,
                mock_loss_reform_context,
                mock_territory_context
            ]
            
            result = mock_computations.trade_period_context()
            
            assert result == mock_territory_context
            assert mock_get_context.call_count == 3
            
            # Verify the dimension calls
            calls = mock_get_context.call_args_list
            
            # First call: BusinessTypeDimension -> Trade
            assert calls[0][0][0] == mock_period_context
            dim1 = calls[0][0][1]
            assert str(dim1.dimension) == str(ET.QName(CT_NS, "BusinessTypeDimension"))
            assert str(dim1.value) == str(ET.QName(CT_NS, "Trade"))
            
            # Second call: LossReformDimension -> Post-lossReform
            assert calls[1][0][0] == mock_trade_context
            dim2 = calls[1][0][1]
            assert str(dim2.dimension) == str(ET.QName(CT_NS, "LossReformDimension"))
            assert str(dim2.value) == str(ET.QName(CT_NS, "Post-lossReform"))
            
            # Third call: TerritoryDimension -> UK
            assert calls[2][0][0] == mock_loss_reform_context
            dim3 = calls[2][0][1]
            assert str(dim3.dimension) == str(ET.QName(CT_NS, "TerritoryDimension"))
            assert str(dim3.value) == str(ET.QName(CT_NS, "UK"))
    
    def test_management_expenses_context(self, mock_computations):
        """Test management_expenses_context method."""
        mock_period_context = Mock()
        mock_expenses_context = Mock()
        
        with patch.object(mock_computations, 'period_context', return_value=mock_period_context), \
             patch.object(mock_computations, 'get_context', return_value=mock_expenses_context) as mock_get_context:
            
            result = mock_computations.management_expenses_context()
            
            assert result == mock_expenses_context
            mock_get_context.assert_called_once_with(
                mock_period_context,
                Dimension(
                    ET.QName(CT_NS, "BusinessTypeDimension"),
                    ET.QName(CT_NS, "ManagementExpenses")
                )
            )
    
    def test_start_method(self, mock_computations):
        """Test start method extracts start date."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "StartOfPeriodCoveredByReturn"): "start_value"
        }
        
        with patch.object(mock_computations, 'company_instant_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value="2023-01-01") as mock_value:
            
            result = mock_computations.start()
            
            assert result == "2023-01-01"
            mock_value.assert_called_once_with("start_value")
    
    def test_end_method(self, mock_computations):
        """Test end method extracts end date."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "EndOfPeriodCoveredByReturn"): "end_value"
        }
        
        with patch.object(mock_computations, 'company_instant_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value="2023-12-31") as mock_value:
            
            result = mock_computations.end()
            
            assert result == "2023-12-31"
            mock_value.assert_called_once_with("end_value")
    
    def test_company_name_method(self, mock_computations):
        """Test company_name method extracts company name."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "CompanyName"): "name_value"
        }
        
        with patch.object(mock_computations, 'company_instant_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value="Test Company Ltd") as mock_value:
            
            result = mock_computations.company_name()
            
            assert result == "Test Company Ltd"
            mock_value.assert_called_once_with("name_value")
    
    def test_tax_reference_method(self, mock_computations):
        """Test tax_reference method extracts tax reference."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "TaxReference"): "tax_ref_value"
        }
        
        with patch.object(mock_computations, 'company_instant_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value="1234567890") as mock_value:
            
            result = mock_computations.tax_reference()
            
            assert result == "1234567890"
            mock_value.assert_called_once_with("tax_ref_value")
    
    def test_company_number_method(self, mock_computations):
        """Test company_number method extracts entity ID."""
        mock_context = Mock()
        mock_entity = Mock()
        mock_entity.id = "12345678"
        mock_context.entity = mock_entity
        
        with patch.object(mock_computations, 'entity_context', return_value=mock_context):
            result = mock_computations.company_number()
            assert result == "12345678"
    
    def test_gross_profit_loss_method(self, mock_computations):
        """Test gross_profit_loss method extracts value from period context."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CORE_NS, "GrossProfitLoss"): "profit_value"
        }
        
        with patch.object(mock_computations, 'period_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value=50000) as mock_value:
            
            result = mock_computations.gross_profit_loss()
            
            assert result == 50000
            mock_value.assert_called_once_with("profit_value")
    
    def test_turnover_revenue_method(self, mock_computations):
        """Test turnover_revenue method extracts value from period context."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CORE_NS, "TurnoverRevenue"): "turnover_value"
        }
        
        with patch.object(mock_computations, 'period_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value=1000000) as mock_value:
            
            result = mock_computations.turnover_revenue()
            
            assert result == 1000000
            mock_value.assert_called_once_with("turnover_value")
    
    def test_sme_rnd_expenditure_deduction_success(self, mock_computations):
        """Test sme_rnd_expenditure_deduction method successful extraction."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "AdjustmentsAdditionalDeductionForQualifyingRDExpenditureSME"): "rnd_value"
        }
        
        with patch.object(mock_computations, 'trade_period_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value=25000) as mock_value:
            
            result = mock_computations.sme_rnd_expenditure_deduction()
            
            assert result == 25000
            mock_value.assert_called_once_with("rnd_value")
    
    def test_sme_rnd_expenditure_deduction_exception(self, mock_computations):
        """Test sme_rnd_expenditure_deduction method handles exceptions."""
        with patch.object(mock_computations, 'trade_period_context', side_effect=Exception("Context error")):
            result = mock_computations.sme_rnd_expenditure_deduction()
            assert result is None
    
    def test_investment_allowance_method(self, mock_computations):
        """Test investment_allowance method extracts value."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "MainPoolAnnualInvestmentAllowance"): "allowance_value"
        }
        
        with patch.object(mock_computations, 'management_expenses_context', return_value=mock_context), \
             patch.object(mock_computations, 'value', return_value=200000) as mock_value:
            
            result = mock_computations.investment_allowance()
            
            assert result == 200000
            mock_value.assert_called_once_with("allowance_value")
    
    def test_type_of_company_method(self, mock_computations):
        """Test type_of_company method returns fixed value."""
        result = mock_computations.type_of_company()
        assert result == 0
    
    def test_repayment_method(self, mock_computations):
        """Test repayment method returns fixed value."""
        result = mock_computations.repayment()
        assert result is False
    
    def test_claiming_earlier_period_relief_method(self, mock_computations):
        """Test claiming_earlier_period_relief method returns fixed value."""
        result = mock_computations.claiming_earlier_period_relief()
        assert result is False
    
    def test_making_more_than_one_return_method(self, mock_computations):
        """Test making_more_than_one_return method returns fixed value."""
        result = mock_computations.making_more_than_one_return()
        assert result is False
    
    def test_estimated_figures_method(self, mock_computations):
        """Test estimated_figures method returns fixed value."""
        result = mock_computations.estimated_figures()
        assert result is False
    
    def test_financial_year_methods(self, mock_computations):
        """Test financial year related methods."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "FinancialYear1CoveredByTheReturn"): "fy1_value",
            ET.QName(CT_NS, "FinancialYear2CoveredByTheReturn"): "fy2_value",
            ET.QName(CT_NS, "FY1AmountOfProfitChargeableAtFirstRate"): "fy1_profit_value",
            ET.QName(CT_NS, "FY2AmountOfProfitChargeableAtFirstRate"): "fy2_profit_value",
            ET.QName(CT_NS, "FY1FirstRateOfTax"): "fy1_rate_value",
            ET.QName(CT_NS, "FY2FirstRateOfTax"): "fy2_rate_value",
            ET.QName(CT_NS, "FY1TaxAtFirstRate"): "fy1_tax_value",
            ET.QName(CT_NS, "FY2TaxAtFirstRate"): "fy2_tax_value",
        }
        
        with patch.object(mock_computations, 'company_period_context', return_value=mock_context), \
             patch.object(mock_computations, 'value') as mock_value:
            
            # Set up return values for each call
            mock_value.side_effect = [2023, 2024, 100000, 50000, 19.0, 25.0, 19000, 12500]
            
            assert mock_computations.fy1() == 2023
            assert mock_computations.fy2() == 2024
            assert mock_computations.fy1_profit() == 100000
            assert mock_computations.fy2_profit() == 50000
            assert mock_computations.fy1_tax_rate() == 19.0
            assert mock_computations.fy2_tax_rate() == 25.0
            assert mock_computations.fy1_tax() == 19000
            assert mock_computations.fy2_tax() == 12500
            
            # Verify all value calls were made
            assert mock_value.call_count == 8
    
    def test_tax_calculation_methods(self, mock_computations):
        """Test tax calculation related methods."""
        mock_context = Mock()
        mock_context.values = {
            ET.QName(CT_NS, "AdjustedTradingProfitOfThisPeriod"): "adjusted_profit_value",
            ET.QName(CT_NS, "NetTradingProfits"): "net_profits_value",
            ET.QName(CT_NS, "NetChargeableGains"): "net_gains_value",
            ET.QName(CT_NS, "ProfitsBeforeOtherDeductionsAndReliefs"): "profits_before_value",
            ET.QName(CT_NS, "ProfitsBeforeChargesAndGroupRelief"): "profits_charges_value",
            ET.QName(CT_NS, "TotalProfitsChargeableToCorporationTax"): "total_profits_value",
            ET.QName(CT_NS, "CorporationTaxChargeable"): "corp_tax_value",
            ET.QName(CT_NS, "TaxChargeable"): "tax_chargeable_value",
            ET.QName(CT_NS, "TaxPayable"): "tax_payable_value",
        }
        
        with patch.object(mock_computations, 'company_period_context', return_value=mock_context), \
             patch.object(mock_computations, 'value') as mock_value:
            
            mock_value.side_effect = [75000, 70000, 5000, 65000, 60000, 55000, 10450, 10450, 10450]
            
            assert mock_computations.adjusted_trading_profit() == 75000
            assert mock_computations.net_trading_profits() == 70000
            assert mock_computations.net_chargeable_gains() == 5000
            assert mock_computations.profits_before_other_deductions_and_reliefs() == 65000
            assert mock_computations.profits_before_charges_and_group_relief() == 60000
            assert mock_computations.total_profits_chargeable_to_corporation_tax() == 55000
            assert mock_computations.corporation_tax_chargeable() == 10450
            assert mock_computations.tax_chargeable() == 10450
            assert mock_computations.tax_payable() == 10450
            
            assert mock_value.call_count == 9
    
    def test_to_values_method_setup(self, mock_computations):
        """Test to_values method generates all definitions - setup patches."""
        # Set up patches for all methods
        patches = [
            patch.object(mock_computations, 'company_name', return_value="Test Company Ltd"),
            patch.object(mock_computations, 'company_number', return_value="12345678"),
            patch.object(mock_computations, 'tax_reference', return_value="1234567890"),
            patch.object(mock_computations, 'type_of_company', return_value=0),
            patch.object(mock_computations, 'start', return_value="2023-01-01"),
            patch.object(mock_computations, 'end', return_value="2023-12-31"),
            patch.object(mock_computations, 'turnover_revenue', return_value=1000000),
            patch.object(mock_computations, 'net_trading_profits', return_value=70000),
            patch.object(mock_computations, 'profits_before_other_deductions_and_reliefs', return_value=65000),
            patch.object(mock_computations, 'profits_before_charges_and_group_relief', return_value=60000),
            patch.object(mock_computations, 'total_profits_chargeable_to_corporation_tax', return_value=55000),
            patch.object(mock_computations, 'fy1', return_value=2023),
            patch.object(mock_computations, 'fy1_profit', return_value=55000),
            patch.object(mock_computations, 'fy1_tax_rate', return_value=19.0),
            patch.object(mock_computations, 'fy1_tax', return_value=10450),
            patch.object(mock_computations, 'fy2', return_value=None),
            patch.object(mock_computations, 'fy2_profit', return_value=None),
            patch.object(mock_computations, 'fy2_tax_rate', return_value=None),
            patch.object(mock_computations, 'fy2_tax', return_value=None),
            patch.object(mock_computations, 'corporation_tax_chargeable', return_value=10450),
            patch.object(mock_computations, 'tax_chargeable', return_value=10450),
            patch.object(mock_computations, 'tax_payable', return_value=10450),
            patch.object(mock_computations, 'sme_rnd_expenditure_deduction', return_value=25000),
            patch.object(mock_computations, 'investment_allowance', return_value=200000)
        ]
        
        # Start all patches
        for p in patches:
            p.start()
        
        try:
            definitions = mock_computations.to_values()
            
            # Verify it returns a list of Definition objects
            assert isinstance(definitions, list)
            assert len(definitions) > 100  # Should have many definitions
            
            # Check that all are Definition instances
            for defn in definitions:
                assert isinstance(defn, Definition)
                assert isinstance(defn.box, int)
                assert isinstance(defn.description, str)
            
            # Check some specific definitions
            defn_dict = {defn.box: defn for defn in definitions}
            
            self._verify_company_information(defn_dict)
            self._verify_financial_data(defn_dict)
            self._verify_rnd_and_allowances(defn_dict)
            self._verify_fixed_values(defn_dict)
            
        finally:
            # Stop all patches
            for p in patches:
                p.stop()
    
    def _verify_company_information(self, defn_dict):
        """Verify company information definitions."""
        assert defn_dict[1].value == "Test Company Ltd"
        assert defn_dict[2].value == "12345678"
        assert defn_dict[3].value == "1234567890"
        assert defn_dict[4].value == 0
        assert defn_dict[30].value == "2023-01-01"
        assert defn_dict[35].value == "2023-12-31"
    
    def _verify_financial_data(self, defn_dict):
        """Verify financial data definitions."""
        assert defn_dict[145].value == 1000000  # Turnover
        assert defn_dict[155].value == 70000    # Trading profits
        assert defn_dict[315].value == 55000    # Chargeable profits
        assert defn_dict[430].value == 10450    # Corporation tax
        assert defn_dict[525].value == 10450    # Tax payable
    
    def _verify_rnd_and_allowances(self, defn_dict):
        """Verify R&D and allowances definitions."""
        assert defn_dict[660].value == 25000    # R&D expenditure
        assert defn_dict[670].value == 25000    # R&D enhanced
        assert defn_dict[690].value == 200000   # Investment allowance
    
    def _verify_fixed_values(self, defn_dict):
        """Verify fixed value definitions."""
        assert defn_dict[80].value is True      # Accounts attached
        assert defn_dict[650].value is True     # SME claim


class TestComputationsConstants:
    """Test constants and namespace definitions."""
    
    def test_namespace_constants(self):
        """Test that namespace constants are correctly defined."""
        from ct600.computations import CT_NS, CORE_NS
        
        assert CT_NS == "http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01"
        assert CORE_NS == "http://xbrl.frc.org.uk/fr/2025-01-01/core"


class TestComputationsIntegration:
    """Integration tests for the computations module."""
    
    def test_qname_creation(self):
        """Test QName creation with namespaces."""
        qname1 = ET.QName(CT_NS, "CompanyName")
        assert str(qname1) == "{http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01}CompanyName"

        qname2 = ET.QName(CORE_NS, "TurnoverRevenue")
        assert str(qname2) == "{http://xbrl.frc.org.uk/fr/2025-01-01/core}TurnoverRevenue"
    
    def test_dimension_creation(self):
        """Test Dimension object creation."""
        dimension = Dimension(
            ET.QName(CT_NS, "BusinessTypeDimension"),
            ET.QName(CT_NS, "Company")
        )
        
        assert dimension.dimension == ET.QName(CT_NS, "BusinessTypeDimension")
        assert dimension.value == ET.QName(CT_NS, "Company")
    
    @patch('ct600.computations.ET.parse')
    @patch('ct600.computations.ixbrl_parse.ixbrl.parse')
    def test_full_initialization_flow(self, mock_ixbrl_parse, mock_et_parse):
        """Test the full initialization flow with real XML parsing."""
        mock_tree = Mock()
        mock_et_parse.return_value = mock_tree
        
        mock_ixbrl = Mock()
        mock_ixbrl_parse.return_value = mock_ixbrl
        
        xml_data = b"<test>xml content</test>"
        comp = Computations(xml_data)
        
        # Verify BytesIO was created and passed to ET.parse
        mock_et_parse.assert_called_once()
        args = mock_et_parse.call_args[0]
        assert isinstance(args[0], BytesIO)
        
        # Verify the tree was passed to IXBRL parser
        mock_ixbrl_parse.assert_called_once_with(mock_tree)
        
        # Verify the IXBRL object was stored
        assert comp.ixbrl == mock_ixbrl
    
    def test_context_chain_integration(self):
        """Test the context chain for trade period context."""
        # Create a mock computations instance for this test
        with patch('ct600.computations.ET.parse'), \
             patch('ct600.computations.ixbrl_parse.ixbrl.parse'):
            
            mock_computations = Computations(b"<test/>")
            
            # This is an integration test for the complex context chaining
            mock_period = Mock()
            mock_trade = Mock()
            mock_loss_reform = Mock()
            mock_territory = Mock()
            
            with patch.object(mock_computations, 'period_context', return_value=mock_period):
                with patch.object(mock_computations, 'get_context') as mock_get_context:
                    mock_get_context.side_effect = [mock_trade, mock_loss_reform, mock_territory]
                    
                    result = mock_computations.trade_period_context()
                    
                    # Should return the final context in the chain
                    assert result == mock_territory
                    
                    # Should have made 3 get_context calls with increasing specificity
                    assert mock_get_context.call_count == 3
                    
                    # Verify the progression of contexts
                    calls = mock_get_context.call_args_list
                    assert calls[0][0][0] == mock_period        # Start with period
                    assert calls[1][0][0] == mock_trade         # Then trade
                    assert calls[2][0][0] == mock_loss_reform   # Then loss reform
    
    def test_error_handling_integration(self):
        """Test error handling across different methods."""
        # Create a mock computations instance for this test
        with patch('ct600.computations.ET.parse'), \
             patch('ct600.computations.ixbrl_parse.ixbrl.parse'):
            
            mock_computations = Computations(b"<test/>")
            
            # Test that various errors are properly handled or propagated
            
            # Test RuntimeError from get_context
            mock_context = Mock()
            mock_context.children = {}
            
            with pytest.raises(RuntimeError):
                mock_computations.get_context(mock_context, "missing_relation")
            
            # Test exception handling in sme_rnd_expenditure_deduction
            with patch.object(mock_computations, 'trade_period_context', side_effect=KeyError("Missing key")):
                result = mock_computations.sme_rnd_expenditure_deduction()
                assert result is None  # Should return None on exception