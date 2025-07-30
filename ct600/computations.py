
from lxml import etree as ET
from io import BytesIO
import ixbrl_parse.ixbrl
from ixbrl_parse.ixbrl import Period, Instant, Entity, Dimension
from ixbrl_parse.value import *

CT_NS = "http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01"
CORE_NS = "http://xbrl.frc.org.uk/fr/2023-01-01/core"

class Definition:
    def __init__(self, box, description):
        self.box = box
        self.description = description
        self.value = None
    def set(self, v):
        self.value = v
        return self

class Computations:

    def __init__(self, comps):
        tree = ET.parse(BytesIO(comps))
        self.ixbrl = ixbrl_parse.ixbrl.parse(tree)

    def get_context(self, ctxt, rel):

        if not rel in ctxt.children:
            raise RuntimeError("No context " + str(rel))

        return ctxt.children[rel]

    def value(self, v):
        return v.to_value().get_value()

    def period_context(self):

        # Find the period context with the latest end date
        p_ctxt = None
        t = None
        for rel, ctxt, lvl in self.ixbrl.context_iter():
            if isinstance(rel, Period):
                if not t or rel.end > t:
                    t = rel.end
                    p_ctxt = ctxt

        if p_ctxt is None:
            raise RuntimeError("Expected to find a period context")

        return p_ctxt

    def instant_context(self):

        # Find the instant context with the latest date
        i_ctxt = None
        t = None
        for rel, ctxt, lvl in self.ixbrl.context_iter():
            if isinstance(rel, Instant):
                if not t or rel.instant > t:
                    t = rel.instant
                    i_ctxt = ctxt

        if i_ctxt is None:
            raise RuntimeError("Expected to find an instant context")

        return i_ctxt

    def entity_context(self):

        # Find the entity context
        e_ctxt = None
        for rel, ctxt, lvl in self.ixbrl.context_iter():
            if isinstance(rel, Entity):
                e_ctxt = ctxt

        if e_ctxt is None:
            raise RuntimeError("Expected to find an entity context")

        return e_ctxt

    def company_instant_context(self):

        ctxt = self.get_context(
            self.instant_context(),
            Dimension(
                ET.QName(CT_NS, "BusinessTypeDimension"),
                ET.QName(CT_NS, "Company")
            )
        )

        return ctxt

    def company_period_context(self):

        ctxt = self.get_context(
            self.period_context(),
            Dimension(
                ET.QName(CT_NS, "BusinessTypeDimension"),
                ET.QName(CT_NS, "Company")
            )
        )

        return ctxt

    def trade_period_context(self):

        ctxt = self.get_context(
            self.period_context(),
            Dimension(
                ET.QName(CT_NS, "BusinessTypeDimension"),
                ET.QName(CT_NS, "Trade")
            )
        )

        ctxt = self.get_context(
            ctxt,
            Dimension(
                ET.QName(CT_NS, "LossReformDimension"),
                ET.QName(CT_NS, "Post-lossReform")
            )
        )

        ctxt = self.get_context(
            ctxt,
            Dimension(
                ET.QName(CT_NS, "TerritoryDimension"),
                ET.QName(CT_NS, "UK")
            )
        )

        return ctxt
    
    def management_expenses_context(self):

        ctxt = self.get_context(
            self.period_context(),
            Dimension(
                ET.QName(CT_NS, "BusinessTypeDimension"),
                ET.QName(CT_NS, "ManagementExpenses")
            )
        )

        return ctxt

    def start(self):
        
        val = self.company_instant_context().values[
            ET.QName(CT_NS, "StartOfPeriodCoveredByReturn")
        ]

        return self.value(val)

    def end(self):
        
        val = self.company_instant_context().values[
            ET.QName(CT_NS, "EndOfPeriodCoveredByReturn")
        ]

        return self.value(val)

    def company_name(self):
        
        val = self.company_instant_context().values[
            ET.QName(CT_NS, "CompanyName")
        ]

        return self.value(val)

    def tax_reference(self):
        
        val = self.company_instant_context().values[
            ET.QName(CT_NS, "TaxReference")
        ]

        return self.value(val)

    def company_number(self):
        
        return self.entity_context().entity.id

    def gross_profit_loss(self):
        
        val = self.period_context().values[
            ET.QName(CORE_NS, "GrossProfitLoss")
        ]

        return self.value(val)

    def turnover_revenue(self):
        qname = ET.QName(CORE_NS, "TurnoverRevenue")

        try:
            # Try the original approach first
            val = self.period_context().values[qname]
            return self.value(val)
        except KeyError:
            # Try to find any QName with localname "TurnoverRevenue"
            context = self.period_context()
            for available_qname in context.values.keys():
                if hasattr(available_qname, 'localname') and available_qname.localname == "TurnoverRevenue":
                    val = context.values[available_qname]
                    return self.value(val)

            # If still not found, return 0
            return "0"

    def adjusted_trading_profit(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "AdjustedTradingProfitOfThisPeriod")
        ]

        return self.value(val)

    def net_trading_profits(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "NetTradingProfits")
        ]

        return self.value(val)

    def net_chargeable_gains(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "NetChargeableGains")
        ]

        return self.value(val)

    def profits_before_other_deductions_and_reliefs(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "ProfitsBeforeOtherDeductionsAndReliefs")
        ]

        return self.value(val)

    def profits_before_charges_and_group_relief(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "ProfitsBeforeChargesAndGroupRelief")
        ]

        return self.value(val)

    def total_profits_chargeable_to_corporation_tax(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "TotalProfitsChargeableToCorporationTax")
        ]

        return self.value(val)

    def fy1(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FinancialYear1CoveredByTheReturn")
        ]

        return self.value(val)

    def fy2(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FinancialYear2CoveredByTheReturn")
        ]

        return self.value(val)

    def fy1_profit(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FY1AmountOfProfitChargeableAtFirstRate")
        ]

        return self.value(val)

    def fy2_profit(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FY2AmountOfProfitChargeableAtFirstRate")
        ]

        return self.value(val)

    def fy1_tax_rate(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FY1FirstRateOfTax")
        ]

        return self.value(val)

    def fy2_tax_rate(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FY2FirstRateOfTax")
        ]

        return self.value(val)

    def fy1_tax(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FY1TaxAtFirstRate")
        ]

        return self.value(val)

    def fy2_tax(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "FY2TaxAtFirstRate")
        ]

        return self.value(val)

    def corporation_tax_chargeable(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "CorporationTaxChargeable")
        ]

        return self.value(val)

    def tax_chargeable(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "TaxChargeable")
        ]

        return self.value(val)

    def tax_payable(self):
        
        val = self.company_period_context().values[
            ET.QName(CT_NS, "TaxPayable")
        ]

        return self.value(val)

    def sme_rnd_expenditure_deduction(self):

        try:
            val = self.trade_period_context().values[
                ET.QName(CT_NS,
                         "AdjustmentsAdditionalDeductionForQualifyingRDExpenditureSME"
                         )
            ]
            return self.value(val)
        except:
            return None

    def investment_allowance(self):

        val = self.management_expenses_context().values[
            ET.QName(CT_NS,
                     "MainPoolAnnualInvestmentAllowance"
            )
        ]

        return self.value(val)

    def type_of_company(self):
        return 0

    def repayment(self):
        return False

    def claiming_earlier_period_relief(self):
        return False

    def making_more_than_one_return(self):
        return False

    def estimated_figures(self):
        return False

    def to_values(self):
        return [
            Definition(1, "Company name").set(self.company_name()),
            Definition(2, "Company registration number").set(
                self.company_number()
            ),
            Definition(3, "Tax reference").set(self.tax_reference()),
            Definition(4, "Type of company").set(self.type_of_company()),
            Definition(30, "Start of return").set(self.start()),
            Definition(35, "End of return").set(self.end()),
            Definition(40, "Repayments this period").set(False),
            Definition(50, "Making more than one return now"),
            Definition(55, "Estimated figures"),
            Definition(60, "Company part of a group that is not small"),
            Definition(65, "Notice of disclosable avoidance schemes"),
            Definition(70, "Compensating adjustment claimed"),
            Definition(75, "Company qualifies for SME exemption"),
            Definition(
                80, "Attached accounts and computations for this period"
            ).set(True),
            Definition(
                85, "Attached accounts and computations for a different period"
            ),
            Definition(90, "Reason for not attaching accounts"),
            Definition(95, "CT600A - Loans and arrangements"),
            Definition(100, "CT600B - Controlled foreign companies"),
            Definition(105, "CT600C - Group & consortium"),
            Definition(110, "CT600D - Insurance"),
            Definition(115, "CT600E - CASCs"),
            Definition(120, "CT600F - Tonnage tax"),
            Definition(125, "CT600G - Northern Ireland"),
            Definition(130, "CT600H - Cross-border royalties"),
            Definition(135, "CT600I - Ring fence trades"),
            Definition(140, "CT600J - Tax avoidance schemes"),
            Definition(141, "CT600K - Restitution"),
            Definition(142, "CT600L - R&D"),
            Definition(143, "CT600M - Freeports"),
            Definition(144, "CT600N - Residential property developer tax"),
            Definition(145, "Total turnover from trade").set(
                self.turnover_revenue()
            ),
            Definition(150, "Banks and other financial concerns"),
            Definition(155, "Trading profits").set(
                self.net_trading_profits()
            ),
            Definition(160, "Trading losses brought forward against profits"),
            Definition(165, "Net trading profits").set(
                self.net_trading_profits()
            ),
            Definition(170, "Bank, building society or other interest, and profits from non-trading loan relationships"),
            Definition(172, "Box 170 net of carrying back deficit"),
            Definition(175, "Annual payments not otherwise charged to Corporation Tax and from which Income Tax has not been deducted"),
            Definition(180, "Non-exempt dividends or distributions from non-UK resident companies"),
            Definition(185, "Income from which Income Tax has been deducted"),
            Definition(190, "Income from a property business"),
            Definition(195, "Non-trading gains on intangible fixed assets"),
            Definition(200, "Tonnage Tax profits"),
            Definition(205, "Income not falling under any other heading"),
            Definition(210, "Gross chargeable gains"),
            Definition(215, "Allowable losses including losses brought forward"),
            Definition(220, "Net chargeable gains"),
            Definition(225, "Losses brought forward against certain investment income"),
            Definition(230, "Non-trade deficits on loan relationships (including interest), and derivative contracts (financial instruments) brought forward set against non-trading profits"),
            Definition(235, "Profits before other deductions and reliefs").set(
                self.profits_before_other_deductions_and_reliefs()
            ),
            Definition(240, "Losses on unquoted shares"),
            Definition(245, "Management expenses"),
            Definition(250, "UK property business losses for this or previous accounting period"),
            Definition(255, "Capital allowances for the purpose of management of the business"),
            Definition(260, "Non-trade deficits for this accounting period from loan relationships and derivative contracts (financial instruments)"),
            Definition(263, "Carried forward non-trade deficits from loan relationships and derivative contracts (financial instruments)"),
            Definition(265, "Non-trading losses on intangible fixed assets"),
            Definition(275, "Trading losses of this or a later accounting period"),
            Definition(280, "Put an X in box 280 if amounts carried back from later accounting periods are included in box 275"),
            Definition(285, "Trading losses carried forward and claimed against total profits"),
            Definition(290, "Non-trade capital allowances"),
            Definition(295, "Total of deductions and reliefs"),
            Definition(
                300, "Profits before qualifying donations and group relief"
            ).set(
                self.profits_before_charges_and_group_relief()
            ),
            Definition(305, "Qualifying donations"),
            Definition(310, "Group relief"),
            Definition(312, "Group relief for carried forward losses"),
            Definition(315, "Profits chargeable to Corporation Tax").set(
                self.total_profits_chargeable_to_corporation_tax()
            ),
            Definition(320, "Ring fence profits included"),
            Definition(325, "Northern Ireland profits included"),
            Definition(326, "Number of associated companies in this period"),
            Definition(327, "Number of associated companies in the 1st FY"),
            Definition(328, "Number of associated companies in the 2nd FY"),
            Definition(329, "Chargeable at the small profit rate"),
            Definition(330, "FY1").set(self.fy1()),
            Definition(335, "FY1 Profit 1").set(self.fy1_profit()),
            Definition(340, "FY1 Rate of Tax 1").set(self.fy1_tax_rate()),
            Definition(345, "FY1 Tax 1").set(self.fy1_tax()),
            Definition(350, "FY1 Profit 2"),
            Definition(355, "FY1 Rate of Tax 2"),
            Definition(360, "FY1 Tax 2"),
            Definition(365, "FY1 Profit 3"),
            Definition(370, "FY1 Rate of Tax 3"),
            Definition(375, "FY1 Tax 3"),
            Definition(380, "FY2").set(self.fy2()),
            Definition(385, "FY2 Profit 1").set(self.fy2_profit()),
            Definition(390, "FY2 Rate of Tax 1").set(self.fy2_tax_rate()),
            Definition(395, "FY2 Tax 1").set(self.fy2_tax()),
            Definition(400, "FY2 Profit 2"),
            Definition(405, "FY2 Rate of Tax 2"),
            Definition(410, "FY2 Tax 2"),
            Definition(415, "FY2 Profit 3"),
            Definition(420, "FY2 Rate of Tax 3"),
            Definition(425, "FY2 Tax 3"),
            Definition(430, "Corporation Tax").set(
                self.corporation_tax_chargeable()
            ),
            Definition(435, "Marginal relief for ring fence trades"),
            Definition(440, "Corporation Tax chargeable").set(
                self.corporation_tax_chargeable()
            ),
            Definition(445, "Community Investment relief"),
            Definition(450, "Double Taxation Relief"),
            Definition(455, "Put an X in box 455 if box 450 includes an underlying Rate relief claim"),
            Definition(460, "Put an X in box 460 if box 450 includes any amount carried back from a later period"),
            Definition(465, "Advance Corporation Tax"),
            Definition(470, "Total reliefs and deduction in terms of tax"),
            Definition(471, "CJRS and Job Support Scheme received"),
            Definition(472, "CJRS and Job Support Scheme entitlement"),
            Definition(473, "CJRS overpayment already assessed or voluntary disclosed"),
            Definition(474, "Other Coronavirus overpayments"),
            Definition(986, "Energy (Oil and Gas) Profits Levy"),
            Definition(475, "Net Corporation Tax liability").set(
                self.corporation_tax_chargeable()
            ),
            Definition(480, "Tax payable on loans and arrangements to participators"),
            Definition(485, "Put an X in box 485 if you completed box A70 in the supplementary pages CT600A"),
            Definition(490, "CFC tax payable"),
            Definition(495, "Bank Levy payable"),
            Definition(496, "Bank surcharge payable"),
            Definition(497, "Residential Property Developer Tax repayable"),
            Definition(500, "CFC tax and bank Levy payable"),
            Definition(501, "EOGPL payable"),
            Definition(505, "Supplementary charge (ring fence trades) payable"),
            Definition(510, "Tax chargeable").set(
                self.tax_chargeable()
            ),
            Definition(515, "Income Tax deducted from gross income included in profits"),
            Definition(520, "Income Tax repayable to the company"),
            Definition(525, "Self-assessment of tax payable before restitution tax and coronavirus support scheme overpayments").set(
                self.tax_payable()
            ),
            Definition(526, "Coronavirus support schemes overpayment now due"),
            Definition(527, "Restitution tax"),
            Definition(528, "Self-assessment of tax payable").set(
                self.tax_payable()
            ),
            Definition(530, "Research and Development credit")
            #.set(
#                self.sme_rnd_expenditure_deduction()
            #)
            ,
            Definition(535, "Not currently used"),
            Definition(540, "Creative tax credit"),
            Definition(
                545, "Total of R&D credit and creative tax credit"
            ),
            Definition(550, "Land remediation tax credit"),
            Definition(555, "Life assurance company tax credit"),
            Definition(560, "Total land remediation and life assurance company tax credit"),
            Definition(565, "Capital allowances first-year tax credit"),
            Definition(570, "Surplus Research and Development credits or creative tax credit payable"),
            Definition(575, "Land remediation or life assurance company tax credit payable"),
            Definition(580, "Capital allowances first-year tax credit payable       "),
            Definition(585, "Ring fence Corporation Tax included and 590 Ring fence supplementary charge included"),
            Definition(586, "NI Corporation Tax included"),
            Definition(595, "Tax already paid (and not already repaid)"),
            Definition(600, "Tax outstanding"),
            Definition(605, "Tax overpaid including surplus or payable credits"),
            Definition(610, "Group tax refunds surrendered to this company"),
            Definition(615, "Research and Development expenditure credits surrendered to this company"),
            Definition(616, "Export: Yes — goods"),
            Definition(617, "Export: Yes — services"),
            Definition(618, "Export: No — neither"),
            Definition(620, "Franked investment income/exempt ABGH distributions"),
            Definition(625, "Number of 51% group companies"),
            Definition(630, "should have made (whether it has or not) instalment payments as a large company under the Corporation Tax (instalment Payments) Regulations 1998"),
            Definition(631, "Should have made (whether it has or not) instalment payments as a very large company under the Corporation Tax (instalment Payments) Regulations 1998"),
            Definition(635, "is within a group payments arrangement for the period"),
            Definition(640, "has written down or sold intangible assets"),
            Definition(645, "has made cross-border royalty payments"),
            Definition(647, "Eat Out to Help Out Scheme: reimbursed discounts included as taxable income"),
            Definition(650, "Put an X in box 650 if the claim is made by a small or medium-sized enterprise (SME), including a SME subcontractor to a large company").set(True),
            Definition(655, "Put an X in box 655 if the claim is made by a large company"),
            Definition(656, "An R&D claim notification form has been submitted"),
            Definition(657, "An additional information form has been submitted"),
            Definition(659, "R&D expenditure qualifying for SME R&D relief"),
            Definition(660, "R&D enhanced expenditure").set(
                self.sme_rnd_expenditure_deduction()
            ),
            Definition(665, "Creative enhanced expenditure"),
            Definition(670, "R&D and creative enhanced expenditure").set(
                self.sme_rnd_expenditure_deduction()
            ),
            Definition(675, "R&D enhanced expenditure of a SME on work sub contracted to it by a large company"),
            Definition(680, "Vaccines research expenditure"),
            Definition(685, "Enter the total enhanced expenditure"),
            Definition(690, "Annual investment allowance").set(
                self.investment_allowance()
            ),
            Definition(691, "Machinery/plant super-deduction — Capital allowances"),
            Definition(692, "Machinery/plant super-deduction — Balancing charges"),
            Definition(693, "Machinery and plant — special rate allowance — Capital allowances"),
            Definition(694, "Machinery and plant — special rate allowance — Balancing charges"),

            Definition(695, "Machinery and plant — special rate pool - Capital allowance"),
            Definition(700, "Machinery and plant — special rate pool - Balancing charges"),

            Definition(705, "Machinery and plant — main pool - Capital allowance"),
            Definition(710, "Machinery and plant — main pool - Balancing charges"),
            Definition(711, "Structures and buildings - Capital allowances"),
            Definition(715, "Business premises renovation - Capital allowances"),
            Definition(720, "Business premises renovation - Balancing charges"),
            Definition(725, "Other allowances and charges - Capital allowances"),
            Definition(730, "Other allowances and charges - Balancing charges"),
            Definition(713, "Electric charge points - Capital allowances"),
            Definition(714, "Electric charge points - Balancing charges"),
            Definition(721, "Enterprise zones - Capital allowances"),
            Definition(722, "Enterprise zones - Balancing charges"),
            Definition(723, "Zero emissions goods vehicles - Capital allowances"),
            Definition(724, "Zero emissions goods vehicles - Balancing charges"),
            Definition(726, "Zero emissions cars - Capital allowances"),
            Definition(727, "Zero emissions cars - Balancing charges"),

            # Not included:
            Definition(735, "Annual Investment Allowance - Capital allowances"),
            
            Definition(736, "Structures and buildings"),
            Definition(740, "Business premises renovation - Capital allowances"),
            Definition(745, "Business premises renovation - Balancing charges"),

            Definition(741, "Machinery and plant — super-deduction - Capital allowances"),
            Definition(742, "Machinery and plant — super-deduction - Balancing charges"),
            Definition(743, "Machinery and plant — special rate allowance - Capital allowances"),
            Definition(744, "Machinery and plant — special rate allowance - Balancing charges"),
            Definition(750, "Other allowances and charges - Capital allowances"),
            Definition(755, "Other allowances and charges - Balancing charges"),
            Definition(737, "Electric charge points - Capital allowances"),
            Definition(738, "Electric charge points - Balancing charges"),

            Definition(746, "Enterprise Zones - Capital allowances"),
            Definition(747, "Enterprise Zones - Balancing charges"),

            Definition(748, "Zero emissions goods vehicles - Capital allowances"),
            Definition(749, "Zero emissions goods vehicles - Balancing charges"),
            Definition(751, "Zero emissions cars - Capital allowances"),
            Definition(752, "Zero emissions cars - Balancing charges"),

            # Qualifying expenditure
            Definition(760, "Machinery and plant on which first-year allowance is claimed"),
            Definition(765, "Designated environmentally friendly machinery and plant"),
            Definition(770, "Machinery and plant on long-life assets and integral features"),
            Definition(771, "Structures and buildings"),
            Definition(772, "Machinery and plant — super-deduction"),
            Definition(773, "Machinery and plant — special rate allowance"),
            Definition(775, "Other machinery and plant"),

            # Losses, deficits, excess amounts
            Definition(
                780, "Losses of trades carried on wholly or partly in the UK"
            ),
            Definition(785, "Losses of trades carried on wholly or partly in the UK (maximum available for surrender as group relief)"),
            Definition(790, "Losses of trades carried on wholly outside the UK (amount)"),
            Definition(795, "Non-trade deficits on loan relationships and derivative contracts (amount)"),
            Definition(800, "Non-trade deficits on loan relationships and derivative contracts (maximum available for surrender as group relief)"),
            Definition(805, "UK property business losses (amount)"),
            Definition(810, "UK property business losses (maximum available for surrender as group relief)"),
            Definition(815, "Overseas property business losses (amount)"),
            Definition(820, "Losses from miscellaneous transactions (amount)"),
            Definition(825, "Capital losses (amount)"),
            Definition(830, "Non-trading losses on intangible fixed assets (amount)"),
            Definition(835, "Non-trading losses on intangible fixed assets (maximum available for surrender as group relief)"),
            Definition(840, "Non-trade capital allowances (maximum available for surrender as group relief)"),
            Definition(845, "Qualifying donations (maximum available for surrender as group relief)"),
            Definition(850, "Management expenses (amount)855 Management expenses (maximum available for surrender as group relief)"),

            # Northern Ireland, leave blank
            Definition(856, "Amount of group relief claimed which relates to NI trading losses used against rest of UK/mainstream profits"),
            Definition(857, "Amount of group relief claimed which relates to NI trading losses used against NI trading profits"),
            Definition(858, "Amount of group relief claimed which relates to rest of UK/mainstream losses used against NI trading profits"),
            Definition(860, "Small Repayments"),
            Definition(865, "Repayment of Corporation Tax"),
            Definition(870, "Repayment of Income Tax"),
            Definition(875, "Payable Research and Development Tax Credit"),
            Definition(880, "Payable research and development expenditure credit"),
            Definition(885, "Payable creative tax credit"),
            Definition(890, "Payable land remediation or life assurance company tax credit"),
            Definition(895, "Payable capital allowances first-year tax credit"),
            Definition(900, "The following amount is to be surrendered"),
            Definition(905, "Joint notice is attached"),
            Definition(910, "Joint notice will follow"),
            Definition(915, "Please stop repayment of the following amount until we send you the Notice"),
            Definition(920, "Name of bank or building society"),
            Definition(925, "Branch sort code"),
            Definition(930, "Account number"),
            Definition(935, "Name of account"),
            Definition(940, "Building society reference"),
            Definition(945, "enter your status, for example company secretary or authorised agent"),
            Definition(950, "enter the name of your company"),
            Definition(955, "enter the name of the nominated person"),
            Definition(960, "enter the address of the nominated person"),
            Definition(965, "enter your reference for the nominated person"),
            Definition(970, "enter your name"),
            Definition(975, "Name"),
            Definition(980, "Date"),
            Definition(985, "Status"),
        ]

